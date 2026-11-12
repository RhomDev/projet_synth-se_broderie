"""Machine simulée : émule le firmware v2 au niveau des octets.

SIMULATION. Rien de ce que renvoie ce module n'est une mesure. Il sert à
développer et tester l'interface tant que le firmware v2 n'est pas flashé.

Il se comporte comme un port série : ``write()`` reçoit des octets, ``read()`` renvoie
les réponses. La physique est intégrée par pas de 1 ms, comme la tâche 1 kHz prévue
dans le firmware. Les courses et la position de départ sont des valeurs fictives.
"""
from __future__ import annotations

import math
import re
import struct
import threading
import time
from dataclasses import dataclass

from .protocol import (
    ACCEL_MAX,
    INT32_MAX,
    INT32_MIN,
    LINE_MAX,
    SPEED_MAX,
    SPEED_SCALE,
    TICK_HZ,
    WATCHDOG_MAX_MS,
    WATCHDOG_MIN_MS,
    Alarm,
    BLOCKING_ALARMS,
    Endstops,
    ErrorCode,
    MachineStatus,
    format_status,
)

DT = 0.001  # pas d'intégration (s), comme la tâche 1 kHz du firmware
MAX_CATCH_UP = 2.0  # au-delà, on n'intègre pas le retard (processus suspendu)
DEFAULT_ACCEL = 80_000
DEFAULT_VMAX = 2_097
DEFAULT_HOME_SPEED = 1_049
V1_BOOT_WINDOW = 70  # valeur de M100 au démarrage du firmware v1 (pas une mesure)

_PARAM = re.compile(r"^([A-Z])(-?\d+)$")
_LEGACY = re.compile(r"^([XY])(-?)(\d*)$")


def fw_to_steps(units: float) -> float:
    return units * TICK_HZ / SPEED_SCALE


def steps_to_fw(steps_per_s: float) -> int:
    return int(round(steps_per_s * SPEED_SCALE / TICK_HZ))


def _approach(value: float, target: float, delta: float) -> float:
    if value < target:
        return min(value + delta, target)
    return max(value - delta, target)


@dataclass
class _Axis:
    travel: float  # µpas entre les contacts min et max (vérité simulée)
    true_pos: float  # µpas depuis le contact min (vérité simulée)
    offset: float = 0.0  # compteur firmware = true_pos - offset
    v: float = 0.0  # vitesse de consigne rampée, µpas/s
    v_eff: float = 0.0  # vitesse réellement appliquée au dernier pas
    mode: str = "idle"  # idle | legacy | speed | move | home
    target_v: float = 0.0
    target_pos: int = 0
    home_phase: str = ""
    home_speed: float = 0.0
    homed: bool = False

    @property
    def counter(self) -> int:
        return int(round(self.true_pos - self.offset))

    @property
    def min_switch(self) -> bool:
        return self.true_pos <= 0.0

    @property
    def max_switch(self) -> bool:
        return self.true_pos >= self.travel

    def halt(self) -> None:
        self.v = self.v_eff = self.target_v = 0.0
        self.mode = "idle"
        self.home_phase = ""

    @property
    def active(self) -> bool:
        return self.mode != "idle"


class SimulatedMachine:
    """Transport simulé : firmware v2 proposé + mécanique fictive."""

    is_simulation = True
    description = "SIMULATION — firmware v2 proposé, aucune machine réelle"

    # Fraction du tour où l'aiguille est hors du tissu (120° à 240°, fiche Plateau XY)
    WINDOW_PHASE = (1 / 3, 2 / 3)

    def __init__(
        self,
        travel_mm: tuple[float, float] = (300.0, 200.0),
        start_mm: tuple[float, float] = (120.0, 80.0),
        steps_per_mm: float = 80.0,
        clock=time.monotonic,
        firmware_version: int = 2,
    ) -> None:
        self._clock = clock
        self._lock = threading.Lock()
        self._spm = steps_per_mm
        self.firmware_version = firmware_version
        if firmware_version == 1:
            self.description = "SIMULATION — firmware v1 actuel, aucune machine réelle"
        self._sew_rpm = 0.0
        self._sew_t0 = 0.0
        self._axes = {
            "X": _Axis(travel=travel_mm[0] * steps_per_mm, true_pos=start_mm[0] * steps_per_mm),
            "Y": _Axis(travel=travel_mm[1] * steps_per_mm, true_pos=start_mm[1] * steps_per_mm),
        }
        self._open = False
        self.link_cut = False  # injection de panne : la liaison ne transmet plus rien
        self._window_open = False
        self._boot()

    # ------------------------------------------------------------- transport

    def open(self) -> None:
        with self._lock:
            self._open = True
            self._boot()  # l'ouverture du port redémarre la carte (DTR)

    def close(self) -> None:
        with self._lock:
            self._open = False

    @property
    def is_open(self) -> bool:
        return self._open

    def write(self, data: bytes) -> None:
        with self._lock:
            if not self._open or self.link_cut:
                return
            self._advance()
            self._feed(data)

    def read(self, timeout: float) -> bytes:
        deadline = self._clock() + timeout
        while True:
            with self._lock:
                if self._open and not self.link_cut:
                    self._advance()
                    if self._out:
                        data = bytes(self._out)
                        self._out.clear()
                        return data
            if self._clock() >= deadline:
                return b""
            time.sleep(0.001)

    # ------------------------------------------------- injection d'événements

    def set_window_open(self, is_open: bool) -> None:
        """Simule les capteurs TCST2300 : ouverture/fermeture de la fenêtre aiguille."""
        with self._lock:
            self._advance()
            self._window_edge(is_open, self._clock())

    def set_sewing_rpm(self, rpm: float) -> None:
        """Simule la machine à coudre qui tourne : fenêtre ouverte 1/3 du tour."""
        with self._lock:
            self._advance()
            self._sew_rpm = max(0.0, rpm)
            self._sew_t0 = self._clock()
            if not rpm:
                self._window_edge(False, self._clock())

    @property
    def sewing_rpm(self) -> float:
        return self._sew_rpm

    def _window_edge(self, is_open: bool, t: float) -> None:
        if is_open and not self._window_open:
            self._window_start = t
        elif not is_open and self._window_open and self._window_start is not None:
            us = int((t - self._window_start) * 1e6)
            self._va = us & 0xFFFFFFFF
            self._m100 = us & 0xFFFF
        self._window_open = is_open

    @property
    def window_open(self) -> bool:
        return self._window_open

    def reboot(self) -> None:
        """Simule un redémarrage de la carte (DTR, coupure, chien de garde matériel)."""
        with self._lock:
            self._boot()

    # ---------------------------------------------------------------- interne

    def _boot(self) -> None:
        now = self._clock()
        self._boot_time = now
        self._last_update = now
        self._last_valid = now
        self._rx = bytearray()
        self._rx_overflow = False
        self._out = bytearray()
        self._manual = False
        self._watchdog_ms = 0
        self._alarms = Alarm.NONE
        self._accel = DEFAULT_ACCEL
        self._vmax = DEFAULT_VMAX
        self._va = 0
        self._m100 = V1_BOOT_WINDOW
        self._window_start = None
        for ax in self._axes.values():
            ax.halt()
            ax.homed = False
            ax.offset = ax.true_pos  # le compteur repart de 0 à la mise sous tension

    def _feed(self, data: bytes) -> None:
        for b in data:
            if b == 0x0A:
                if self._rx_overflow:
                    self._reply("err M0 7")
                else:
                    self._execute(self._rx.decode("ascii", errors="replace"))
                self._rx.clear()
                self._rx_overflow = False
            elif b == 0x0D:
                continue
            elif len(self._rx) < LINE_MAX:
                self._rx.append(b)
            else:
                self._rx_overflow = True

    def _reply(self, text: str) -> None:
        self._out += (text + "\n").encode("ascii")

    def _execute(self, line: str) -> None:
        text = line.strip()
        if not text:
            return
        if text[0] in "XY":
            self._last_valid = self._clock()
            self._legacy_speeds(text)
            return
        v1 = self.firmware_version == 1
        if text[0] != "M":
            if not v1:  # le firmware v1 ignore sans répondre
                self._reply("err M0 7")
            return
        tokens = text.split()
        head = re.match(r"^M(\d+)$", tokens[0])
        if not head:
            if not v1:
                self._reply("err M0 7")
            return
        code = int(head.group(1))
        if v1 and code not in (100, 101, 102):
            return
        params: dict[str, int] = {}
        for tok in tokens[1:]:
            m = _PARAM.match(tok)
            if not m:
                self._reply(f"err M{code} 7")
                return
            params[m.group(1)] = int(m.group(2))
        self._last_valid = self._clock()
        if code == 100:
            self._out += struct.pack("<H", self._m100)
        elif code == 101:
            self._out.append(self._endstops().to_bits())
        elif code == 102:
            self._out.append(int(self._window_open))
        else:
            handler = getattr(self, f"_m{code}", None)
            if handler is None:
                self._reply(f"err M{code} {int(ErrorCode.UNKNOWN_COMMAND)}")
            else:
                self._reply(handler(params))

    def _legacy_speeds(self, text: str) -> None:
        """Lignes v1 ``X100 Y-200`` : vitesse immédiate, sans réponse."""
        if self._alarms & BLOCKING_ALARMS:
            return  # précision v2 : ignorées tant qu'une alarme bloquante est active
        for word in text.split():
            m = _LEGACY.match(word)
            if not m:
                continue
            value = int(m.group(3) or 0) & 0xFFFF
            value = min(value, SPEED_MAX)  # au-delà, le firmware réel devient erratique
            ax = self._axes[m.group(1)]
            if self._home_active():
                continue
            ax.mode = "legacy" if value else "idle"
            ax.target_v = ax.v = fw_to_steps(value) * (-1 if m.group(2) else 1)

    # ------------------------------------------------------------ commandes v2

    def _err(self, code: int, err: ErrorCode) -> str:
        return f"err M{code} {int(err)}"

    def _motion_guard(self, code: int) -> str | None:
        if not self._manual:
            return self._err(code, ErrorCode.MANUAL_MODE_ONLY)
        if self._alarms & BLOCKING_ALARMS:
            return self._err(code, ErrorCode.ALARM_ACTIVE)
        if self._home_active():
            return self._err(code, ErrorCode.HOMING_IN_PROGRESS)
        return None

    def _home_active(self) -> bool:
        return any(ax.mode == "home" for ax in self._axes.values())

    @staticmethod
    def _only(params: dict[str, int], allowed: str) -> bool:
        return all(k in allowed for k in params)

    def _m110(self, p: dict[str, int]) -> str:
        for ax in self._axes.values():
            ax.halt()
        return "ok M110"

    def _m111(self, p: dict[str, int]) -> str:
        return format_status(self.snapshot())

    def _m112(self, p: dict[str, int]) -> str:
        if not self._only(p, "S") or p.get("S") not in (0, 1):
            return self._err(112, ErrorCode.BAD_PARAMETER)
        if not p["S"]:  # comme le firmware : les mouvements v2 sont réservés au mode manuel
            for ax in self._axes.values():
                if ax.mode in ("speed", "move", "home"):
                    ax.halt()
        self._manual = bool(p["S"])
        return f"ok M112 S{int(self._manual)}"

    def _m113(self, p: dict[str, int]) -> str:
        t = p.get("T")
        if not self._only(p, "T") or t is None or not (t == 0 or WATCHDOG_MIN_MS <= t <= WATCHDOG_MAX_MS):
            return self._err(113, ErrorCode.BAD_PARAMETER)
        self._watchdog_ms = t
        return f"ok M113 T{t}"

    def _m114(self, p: dict[str, int]) -> str:
        self._alarms = Alarm.NONE
        return "ok M114"

    def _m120(self, p: dict[str, int]) -> str:
        if err := self._motion_guard(120):
            return err
        if not p or not self._only(p, "XY") or any(abs(v) > SPEED_MAX for v in p.values()):
            return self._err(120, ErrorCode.BAD_PARAMETER)
        for name, value in p.items():
            ax = self._axes[name]
            ax.mode = "speed" if value else ("speed" if ax.v else "idle")
            ax.target_v = fw_to_steps(value)
        tx = steps_to_fw(self._axes["X"].target_v)
        ty = steps_to_fw(self._axes["Y"].target_v)
        return f"ok M120 X{tx} Y{ty}"

    def _m121(self, p: dict[str, int]) -> str:
        if not p or not self._only(p, "AV"):
            return self._err(121, ErrorCode.BAD_PARAMETER)
        if "A" in p and not 1 <= p["A"] <= ACCEL_MAX:
            return self._err(121, ErrorCode.BAD_PARAMETER)
        if "V" in p and not 1 <= p["V"] <= SPEED_MAX:
            return self._err(121, ErrorCode.BAD_PARAMETER)
        self._accel = p.get("A", self._accel)
        self._vmax = p.get("V", self._vmax)
        return f"ok M121 A{self._accel} V{self._vmax}"

    def _move(self, code: int, p: dict[str, int], relative: bool) -> str:
        if err := self._motion_guard(code):
            return err
        if not p or not self._only(p, "XY") or any(not INT32_MIN <= v <= INT32_MAX for v in p.values()):
            return self._err(code, ErrorCode.BAD_PARAMETER)
        if not relative and any(not self._axes[n].homed for n in p):
            return self._err(code, ErrorCode.NOT_HOMED)
        for name, value in p.items():
            ax = self._axes[name]
            target = ax.counter + value if relative else value
            ax.target_pos = max(INT32_MIN, min(INT32_MAX, target))
            ax.mode = "move"
        args = " ".join(f"{n}{v}" for n, v in p.items())
        return f"ok M{code} {args}"

    def _m122(self, p: dict[str, int]) -> str:
        return self._move(122, p, relative=True)

    def _m123(self, p: dict[str, int]) -> str:
        return self._move(123, p, relative=False)

    def _m130(self, p: dict[str, int]) -> str:
        if err := self._motion_guard(130):
            return err
        if not self._only(p, "XYF"):
            return self._err(130, ErrorCode.BAD_PARAMETER)
        hx, hy = p.get("X", 0), p.get("Y", 0)
        f = p.get("F", DEFAULT_HOME_SPEED)
        if hx not in (0, 1) or hy not in (0, 1) or not (hx or hy) or not 1 <= f <= SPEED_MAX:
            return self._err(130, ErrorCode.BAD_PARAMETER)
        for name, flag in (("X", hx), ("Y", hy)):
            if flag:
                ax = self._axes[name]
                ax.mode, ax.home_phase, ax.home_speed = "home", "seek", fw_to_steps(f)
                ax.homed = False
        return f"ok M130 X{hx} Y{hy} F{f}"

    # ---------------------------------------------------------------- physique

    def _endstops(self) -> Endstops:
        x, y = self._axes["X"], self._axes["Y"]
        return Endstops(x.min_switch, x.max_switch, y.min_switch, y.max_switch)

    def _advance(self) -> None:
        now = self._clock()
        elapsed = now - self._last_update
        if elapsed > MAX_CATCH_UP:
            self._last_update = now - MAX_CATCH_UP
            elapsed = MAX_CATCH_UP
        steps = int(elapsed / DT)
        for i in range(steps):
            t = self._last_update + (i + 1) * DT
            self._tick(t)
        self._last_update += steps * DT

    def _tick(self, t: float) -> None:
        if self._sew_rpm:
            phase = ((t - self._sew_t0) * self._sew_rpm / 60.0) % 1.0
            lo, hi = self.WINDOW_PHASE
            is_open = lo <= phase < hi
            if is_open != self._window_open:
                self._window_edge(is_open, t)
        if (
            self._watchdog_ms
            and t - self._last_valid > self._watchdog_ms / 1000
            and any(ax.active for ax in self._axes.values())
        ):
            for ax in self._axes.values():
                ax.halt()
            self._alarms |= Alarm.WATCHDOG
        for name, ax in self._axes.items():
            self._tick_axis(name, ax)

    def _tick_axis(self, name: str, ax: _Axis) -> None:
        a = float(self._accel)
        vmax = fw_to_steps(self._vmax)
        if ax.mode == "speed":
            ax.v = _approach(ax.v, ax.target_v, a * DT)
            if ax.target_v == 0 and ax.v == 0:
                ax.mode = "idle"
        elif ax.mode == "move":
            remaining = ax.target_pos - (ax.true_pos - ax.offset)
            direction = 1.0 if remaining > 0 else -1.0
            v_stop = math.sqrt(2 * a * abs(remaining))
            ax.v = _approach(ax.v, direction * min(vmax, v_stop), a * DT)
            if abs(remaining) < 0.5 or (ax.v * direction > 0 and abs(ax.v * DT) >= abs(remaining)):
                ax.true_pos = ax.target_pos + ax.offset
                ax.v = ax.v_eff = 0.0
                ax.mode = "idle"
                return
        elif ax.mode == "home":
            if ax.home_phase == "seek":
                ax.v = _approach(ax.v, -ax.home_speed, a * DT)
                if ax.min_switch:
                    ax.v = 0.0
                    ax.home_phase = "backoff"
            if ax.home_phase == "backoff":
                ax.v = ax.home_speed / 4
                if not ax.min_switch:
                    ax.v = ax.v_eff = 0.0
                    ax.offset = ax.true_pos
                    ax.homed = True
                    ax.mode, ax.home_phase = "idle", ""
                    return
        elif ax.mode == "idle":
            ax.v = 0.0

        allowed_by_window = self._manual or self._window_open
        blocked_by_switch = (ax.v > 0 and ax.max_switch) or (ax.v < 0 and ax.min_switch)
        if blocked_by_switch and ax.mode in ("speed", "move"):
            ax.halt()
            self._alarms |= Alarm.LIMIT_X if name == "X" else Alarm.LIMIT_Y
            return
        if blocked_by_switch or not allowed_by_window:
            ax.v_eff = 0.0  # v1 : la consigne reste mémorisée, aucun pas n'est émis
            return
        ax.v_eff = ax.v
        ax.true_pos += ax.v * DT

    def snapshot(self) -> MachineStatus:
        """État courant au format de la ligne M111 (appelé sous verrou)."""
        x, y = self._axes["X"], self._axes["Y"]
        return MachineStatus(
            t_ms=int((self._clock() - self._boot_time) * 1000) & 0xFFFFFFFF,
            x=x.counter,
            y=y.counter,
            vx=steps_to_fw(x.v_eff),
            vy=steps_to_fw(y.v_eff),
            endstops=self._endstops(),
            window_open=self._window_open,
            manual_mode=self._manual,
            homed_x=x.homed,
            homed_y=y.homed,
            moving_x=x.active,
            moving_y=y.active,
            alarms=self._alarms,
            window_us=self._va,
        )
