"""Liaison avec la carte : seul composant qui touche au port (réel ou simulé).

Elle tourne dans son propre thread pour ne jamais bloquer l'interface :
- file de commandes ; l'arrêt (M110) passe devant et annule les mouvements en attente ;
- une seule requête en vol : la réponse attendue est toujours connue ;
- délai d'attente par réponse, détection de perte de liaison ;
- interrogation périodique de l'état (M111), qui réarme aussi le chien de garde ;
- journal de tous les échanges (signal ``traffic`` et module ``logging``).

Le transport doit offrir ``open()``, ``close()``, ``write(bytes)``, ``read(timeout)``
et les attributs ``is_simulation`` et ``description``.
"""
from __future__ import annotations

import itertools
import logging
import threading
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from PySide6.QtCore import QThread, Signal

from .protocol import (
    V1_ENDSTOPS,
    V1_WINDOW_DURATION,
    V1_WINDOW_OPEN,
    Command,
    MachineStatus,
    ProtocolError,
    Reply,
    V1Query,
    V1Status,
    decode_endstops_v1,
    decode_window_duration_v1,
    decode_window_open_v1,
    parse_reply,
    read_status,
)

log = logging.getLogger("brodeuse.liaison")


class Transport(Protocol):
    is_simulation: bool
    description: str

    def open(self) -> None: ...
    def close(self) -> None: ...
    def write(self, data: bytes) -> None: ...
    def read(self, timeout: float) -> bytes: ...


class LinkState(Enum):
    DISCONNECTED = "Déconnecté"
    CONNECTING = "Connexion…"
    CONNECTED = "Connecté"
    LOST = "Liaison perdue"


class Outcome(Enum):
    CONFIRMED = "confirmée"
    SENT = "envoyée (sans accusé, v1)"
    REJECTED = "refusée"
    TIMEOUT = "sans réponse"
    CANCELLED = "annulée"
    PROTOCOL_ERROR = "réponse incohérente"


@dataclass(frozen=True)
class CommandResult:
    request_id: int
    command: Command
    outcome: Outcome
    reply: Reply | None = None
    detail: str = ""


@dataclass
class _Pending:
    request_id: int
    command: Command


class MachineLink(QThread):
    """Protocole détecté à l'ouverture (attribut ``protocol``) :
    2 = firmware v2 (pilotage complet) ; 1 = firmware v1 (diagnostic : lecture des
    capteurs seulement, aucune commande de mouvement n'est transmise)."""

    status_received = Signal(object)  # MachineStatus
    v1_status_received = Signal(object)  # V1Status
    command_finished = Signal(object)  # CommandResult
    state_changed = Signal(object)  # LinkState
    traffic = Signal(str, str, bool)  # sens (TX/RX/INFO), texte, interrogation périodique

    HANDSHAKE_ATTEMPTS = 3

    def __init__(
        self,
        transport: Transport,
        poll_hz: float = 20.0,
        reply_timeout: float = 0.2,
        lost_after: int = 3,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.transport = transport
        self._poll_period = 1.0 / poll_hz
        self._reply_timeout = reply_timeout
        self._lost_after = lost_after
        self._queue: deque[_Pending] = deque()
        self._cond = threading.Condition()
        self._ids = itertools.count(1)
        self._running = True
        self._closing = False
        self._rx = bytearray()
        self._timeouts = 0
        self._state = LinkState.DISCONNECTED
        self.protocol = 0
        self._v1_window: int | None = None
        self._v1_polls = 0

    # ------------------------------------------------------ API (thread UI)

    @property
    def is_simulation(self) -> bool:
        return bool(getattr(self.transport, "is_simulation", False))

    @property
    def state(self) -> LinkState:
        return self._state

    def submit(self, command: Command, urgent: bool = False) -> int:
        """Met une commande en file ; renvoie son identifiant. Résultat : ``command_finished``."""
        pending = _Pending(next(self._ids), command)
        cancelled: list[_Pending] = []
        with self._cond:
            if urgent:
                if command.code == 110:  # arrêt : les mouvements en attente n'ont plus de sens
                    keep = [p for p in self._queue if not p.command.is_motion]
                    cancelled = [p for p in self._queue if p.command.is_motion]
                    self._queue = deque(keep)
                self._queue.appendleft(pending)
            else:
                self._queue.append(pending)
            self._cond.notify()
        for p in cancelled:
            self._finish(p, Outcome.CANCELLED, detail="annulée par l'arrêt")
        return pending.request_id

    def shutdown(self) -> None:
        """Termine la liaison après avoir envoyé les commandes déjà en file."""
        with self._cond:
            self._closing = True
            self._cond.notify()

    def abort(self) -> None:
        """Termine la liaison immédiatement (commandes en file annulées)."""
        with self._cond:
            self._running = False
            self._cond.notify()

    # ------------------------------------------------------------ thread

    def run(self) -> None:
        self._set_state(LinkState.CONNECTING)
        self._info(f"Ouverture : {getattr(self.transport, 'description', 'transport')}")
        try:
            self.transport.open()
        except Exception as exc:  # port absent, droits, etc.
            self._info(f"Échec d'ouverture : {exc}")
            self._set_state(LinkState.DISCONNECTED)
            return
        try:
            self.protocol = self.detect_protocol()
            if self.protocol == 2:
                self._info("Firmware v2 détecté (M111 répond)")
            elif self.protocol == 1:
                self._info("Firmware v1 détecté (M101/M102 répondent, pas M111) : mode diagnostic, "
                           "lecture des capteurs seulement")
            if self.protocol:
                self._set_state(LinkState.CONNECTED)
                self._loop()
            else:
                self._info("La carte ne répond ni à M111 (v2) ni à M101 (v1). Liaison fermée.")
        finally:
            self._cancel_all("liaison fermée")
            try:
                self.transport.close()
            finally:
                self._set_state(LinkState.DISCONNECTED)
                self._info("Liaison fermée")

    def detect_protocol(self) -> int:
        """2 si M111 répond, 1 si seules les requêtes binaires v1 répondent, 0 sinon.
        M111 envoyé à un firmware v1 est ignoré sans effet."""
        for _ in range(self.HANDSHAKE_ATTEMPTS):
            if not self._running:
                return 0
            if self._transact(_Pending(0, read_status()), poll=True).outcome is Outcome.CONFIRMED:
                return 2
        self._timeouts = 0
        for _ in range(self.HANDSHAKE_ATTEMPTS):
            if not self._running:
                return 0
            es = self._query_v1(V1_ENDSTOPS, decode_endstops_v1, poll=True)
            win = self._query_v1(V1_WINDOW_OPEN, decode_window_open_v1, poll=True)
            if es is not None and win is not None:
                self._timeouts = 0
                return 1
        return 0

    def _loop(self) -> None:
        next_poll = time.monotonic()
        while self._running:
            with self._cond:
                if self._closing and not self._queue:
                    return
                wait = next_poll - time.monotonic()
                if not self._queue and wait > 0:
                    self._cond.wait(wait)
                pending = self._queue.popleft() if self._queue else None
            if not self._running:
                return
            if pending is not None:
                if self.protocol == 1:
                    self._finish(pending, Outcome.CANCELLED, detail="firmware v1 : aucune commande transmise")
                    continue
                if self._state is LinkState.LOST and pending.command.code != 110:
                    self._finish(pending, Outcome.CANCELLED, detail="liaison perdue")
                    continue
                self._finish_result(self._transact(pending, poll=False))
            if time.monotonic() >= next_poll:
                if self.protocol == 2:
                    self._transact(_Pending(0, read_status()), poll=True)
                else:
                    self._poll_v1()
                next_poll = time.monotonic() + self._poll_period

    def _poll_v1(self) -> None:
        es = self._query_v1(V1_ENDSTOPS, decode_endstops_v1, poll=True)
        win = self._query_v1(V1_WINDOW_OPEN, decode_window_open_v1, poll=True)
        if self._v1_polls % 20 == 0:  # M100 environ une fois par seconde
            duration = self._query_v1(V1_WINDOW_DURATION, decode_window_duration_v1, poll=True)
            if duration is not None:
                self._v1_window = duration
        self._v1_polls += 1
        if es is not None and win is not None:
            if self._state is LinkState.LOST:
                self._info("Liaison rétablie")
                self._set_state(LinkState.CONNECTED)
            self.v1_status_received.emit(V1Status(es, win, self._v1_window))

    def _query_v1(self, query: V1Query, decode, poll: bool):
        """Requête v1 à réponse binaire de longueur fixe ; None si absente ou invalide."""
        self._drain()
        try:
            self.transport.write(query.payload)
        except Exception as exc:
            self._info(f"Erreur d'écriture : {exc}")
            return None
        self._emit_traffic("TX", query.payload.decode("ascii").strip(), poll)
        deadline = time.monotonic() + self._reply_timeout
        while len(self._rx) < query.reply_length:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self._timeout(_Pending(0, read_status()))
                return None
            try:
                self._rx += self.transport.read(min(remaining, 0.02))
            except Exception as exc:
                self._info(f"Erreur de lecture : {exc}")
                return None
        raw = bytes(self._rx[: query.reply_length])
        del self._rx[: query.reply_length]
        self._emit_traffic("RX", raw.hex(" "), poll)
        try:
            value = decode(raw)
        except ProtocolError as exc:
            self._info(f"Réponse v1 invalide : {exc}. Tampon vidé.")
            self._rx.clear()
            self._drain()
            return None
        self._timeouts = 0
        return value

    # -------------------------------------------------------- échanges

    def _transact(self, pending: _Pending, poll: bool) -> CommandResult:
        command = pending.command
        self._drain()
        data = command.encode()
        try:
            self.transport.write(data)
        except Exception as exc:
            self._info(f"Erreur d'écriture : {exc}")
            return self._timeout(pending)
        self._emit_traffic("TX", data.decode("ascii").strip(), poll)
        if not getattr(command, "expects_reply", True):
            return CommandResult(pending.request_id, command, Outcome.SENT,
                                 detail="ligne v1 : aucun accusé possible")
        line = self._read_line(time.monotonic() + self._reply_timeout)
        if line is None:
            return self._timeout(pending)
        self._emit_traffic("RX", line, poll)
        try:
            reply = parse_reply(line)
            if reply.code != command.code:
                raise ProtocolError(f"réponse à M{reply.code} reçue pour {command.name}")
            status = MachineStatus.from_reply(reply) if (reply.ok and reply.code == 111) else None
        except ProtocolError as exc:
            self._info(f"Désynchronisation : {exc}. Tampon vidé.")
            self._rx.clear()
            self._drain()
            return CommandResult(pending.request_id, command, Outcome.PROTOCOL_ERROR, detail=str(exc))
        self._timeouts = 0
        if self._state is LinkState.LOST:
            self._info("Liaison rétablie")
            self._set_state(LinkState.CONNECTED)
        if status is not None:
            self.status_received.emit(status)
        outcome = Outcome.CONFIRMED if reply.ok else Outcome.REJECTED
        return CommandResult(pending.request_id, command, outcome, reply, reply.error_text)

    def _timeout(self, pending: _Pending) -> CommandResult:
        self._timeouts += 1
        if self._timeouts >= self._lost_after and self._state is LinkState.CONNECTED:
            self._info(f"{self._timeouts} réponses manquantes : liaison perdue")
            self._set_state(LinkState.LOST)
        return CommandResult(pending.request_id, pending.command, Outcome.TIMEOUT,
                             detail=f"pas de réponse en {self._reply_timeout * 1000:.0f} ms")

    def _read_line(self, deadline: float) -> str | None:
        while True:
            idx = self._rx.find(b"\n")
            if idx >= 0:
                raw = bytes(self._rx[:idx])
                del self._rx[: idx + 1]
                return raw.decode("ascii", errors="replace").strip()
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            try:
                chunk = self.transport.read(min(remaining, 0.02))
            except Exception as exc:
                self._info(f"Erreur de lecture : {exc}")
                return None
            self._rx += chunk

    def _drain(self) -> None:
        """Jette les octets arrivés hors requête (réponse tardive) avant d'envoyer."""
        try:
            stale = self._rx + self.transport.read(0)
        except Exception:
            stale = self._rx
        if stale:
            self._info(f"Octets inattendus ignorés : {bytes(stale)!r}")
        self._rx = bytearray()

    # ------------------------------------------------------------ outils

    def _finish_result(self, result: CommandResult) -> None:
        self.command_finished.emit(result)
        level = logging.INFO if result.outcome is Outcome.CONFIRMED else logging.WARNING
        log.log(level, "%s : %s %s", result.command, result.outcome.value, result.detail)

    def _finish(self, pending: _Pending, outcome: Outcome, detail: str = "") -> None:
        self._finish_result(CommandResult(pending.request_id, pending.command, outcome, detail=detail))

    def _cancel_all(self, reason: str) -> None:
        with self._cond:
            pending, self._queue = list(self._queue), deque()
        for p in pending:
            self._finish(p, Outcome.CANCELLED, detail=reason)

    def _set_state(self, state: LinkState) -> None:
        if state is not self._state:
            self._state = state
            self.state_changed.emit(state)

    def _emit_traffic(self, direction: str, text: str, poll: bool) -> None:
        self.traffic.emit(direction, text, poll)
        if not poll:
            log.debug("%s %s", direction, text)

    def _info(self, text: str) -> None:
        self.traffic.emit("INFO", text, False)
        log.info(text)
