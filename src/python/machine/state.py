"""État de la machine vu par l'application.

L'état est déduit de la liaison et de la dernière ligne d'état reçue. Une ligne
d'état trop ancienne rend l'état « inconnu » : on n'affiche jamais une ancienne
mesure comme si elle était actuelle, et on interdit alors les déplacements.
"""
from __future__ import annotations

import time
from enum import Enum

from PySide6.QtCore import QObject, Signal

from communication.link import LinkState
from communication.protocol import ALARM_TEXT, Alarm, MachineStatus, V1Status


class MachineState(Enum):
    # (libellé, niveau d'affichage : ok / warning / error / inactive / active)
    DISCONNECTED = ("Déconnecté", "inactive")
    CONNECTING = ("Connexion…", "warning")
    LOST = ("Liaison perdue", "error")
    STALE = ("État inconnu", "error")
    ALARM = ("Alarme", "error")
    V1_DIAGNOSTIC = ("Firmware v1 : diagnostic", "warning")
    EMBROIDERY = ("Mode broderie", "active")
    HOMING = ("Prise d'origine", "active")
    MOVING = ("En mouvement", "active")
    UNREFERENCED = ("Origine inconnue", "warning")
    READY = ("Prêt", "ok")

    @property
    def label(self) -> str:
        return self.value[0]

    @property
    def level(self) -> str:
        return self.value[1]


def derive_state(
    link_state: LinkState,
    status: MachineStatus | None,
    fresh: bool,
    homing_requested: bool,
    protocol: int = 2,
) -> MachineState:
    if link_state is LinkState.DISCONNECTED:
        return MachineState.DISCONNECTED
    if link_state is LinkState.CONNECTING:
        return MachineState.CONNECTING
    if link_state is LinkState.LOST:
        return MachineState.LOST
    if protocol == 1:
        return MachineState.V1_DIAGNOSTIC if fresh else MachineState.STALE
    if status is None or not fresh:
        return MachineState.STALE
    if status.blocking_alarm:
        return MachineState.ALARM
    if not status.manual_mode:
        return MachineState.EMBROIDERY
    if homing_requested and status.moving:
        return MachineState.HOMING
    if status.moving:
        return MachineState.MOVING
    if status.homed:
        return MachineState.READY
    return MachineState.UNREFERENCED


class MachineModel(QObject):
    """Dernier état connu + état déduit. Vit dans le thread de l'interface."""

    changed = Signal()
    alarm_raised = Signal(str)
    reboot_detected = Signal()

    def __init__(self, stale_after_s: float = 0.5, parent=None) -> None:
        super().__init__(parent)
        self.stale_after_s = stale_after_s
        self.link_state = LinkState.DISCONNECTED
        self.status: MachineStatus | None = None
        self.status_time = 0.0
        self.simulation = False
        self.homing_requested = False
        self.watchdog_ms = 0  # valeur confirmée par la carte (0 = coupé)
        self.protocol = 0  # 2 = firmware v2, 1 = firmware v1 (diagnostic), 0 = inconnu
        self.v1_status: V1Status | None = None
        self.port_description = ""
        self._state = MachineState.DISCONNECTED

    # ------------------------------------------------------------ entrées

    def set_link_state(self, state: LinkState, protocol: int | None = None) -> None:
        self.link_state = state
        if protocol is not None:
            self.protocol = protocol
        if state is LinkState.DISCONNECTED:
            self.status = None
            self.v1_status = None
            self.protocol = 0
            self.homing_requested = False
            self.watchdog_ms = 0
        self._refresh(force=True)

    def update_v1_status(self, status: V1Status) -> None:
        self.v1_status = status
        self.status_time = time.monotonic()
        self._refresh(force=True)

    def update_status(self, status: MachineStatus) -> None:
        previous = self.status
        if previous is not None and status.t_ms < previous.t_ms:
            self.homing_requested = False
            self.reboot_detected.emit()
        new_alarms = status.alarms & ~(previous.alarms if previous else Alarm.NONE)
        for flag, text in ALARM_TEXT.items():
            if new_alarms & flag:
                self.alarm_raised.emit(text)
        if self.homing_requested and not status.moving:
            self.homing_requested = False
        self.status = status
        self.status_time = time.monotonic()
        self._refresh(force=True)

    def tick(self) -> None:
        """À appeler régulièrement : fait passer l'état à « inconnu » si les données vieillissent."""
        self._refresh(force=False)

    # ------------------------------------------------------------ sorties

    @property
    def fresh(self) -> bool:
        has_data = self.v1_status is not None if self.protocol == 1 else self.status is not None
        return has_data and time.monotonic() - self.status_time <= self.stale_after_s

    @property
    def state(self) -> MachineState:
        return self._state

    @property
    def connected(self) -> bool:
        return self.link_state is LinkState.CONNECTED

    def _refresh(self, force: bool) -> None:
        state = derive_state(self.link_state, self.status, self.fresh, self.homing_requested, self.protocol)
        if force or state is not self._state:
            self._state = state
            self.changed.emit()
