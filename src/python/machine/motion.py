"""Traduction des intentions de l'opérateur en commandes, après contrôle de sécurité.

Jog continu :
- avant l'origine : consigne de vitesse (M120), vitesse plafonnée, les fins de course
  protègent ;
- après l'origine (course connue) : déplacement absolu (M123) vers la limite logicielle
  dans le sens demandé. Même si le PC se fige, la carte s'arrête à la limite.
Le relâchement du bouton envoie M120 X0/Y0 : arrêt sur rampe, qui remplace le
mouvement en cours.
"""
from __future__ import annotations

import logging
import time

from PySide6.QtCore import QObject, Signal

from communication import protocol as p
from communication.link import CommandResult, LinkState, MachineLink, Outcome
from communication.protocol import MachineStatus

from .config import AppConfig, save_config
from .safety import can_home, can_move, check_relative, check_target, soft_bounds, speed_cap
from .state import MachineModel

log = logging.getLogger("brodeuse.mouvement")

CALIBRATION_TIMEOUT_S = 300.0


class MotionController(QObject):
    message = Signal(str, str)  # niveau (info, warning, error), texte
    command_status = Signal(str, str)  # commande, statut (envoyée, confirmée, refusée…)
    calibration_changed = Signal(str)  # avancement ; chaîne vide = terminé
    config_changed = Signal()

    def __init__(self, model: MachineModel, config: AppConfig, parent=None) -> None:
        super().__init__(parent)
        self.model = model
        self.config = config
        self._link: MachineLink | None = None
        self._sent: dict[int, p.Command] = {}
        self._last_limits: tuple[int, int] | None = None
        self._jog = (0, 0)
        self._initialized = False
        self._homing = False
        self._calib: dict | None = None
        self.jog_speed_mm_s = config.manual.speed_mm_s
        self.jog_accel_mm_s2 = config.manual.accel_mm_s2
        model.reboot_detected.connect(self._on_reboot)

    # ------------------------------------------------------------ liaison

    def attach(self, link: MachineLink) -> None:
        self._link = link
        self._initialized = False
        self._last_limits = None
        link.command_finished.connect(self._on_result)
        link.state_changed.connect(self._on_link_state)

    def detach(self) -> None:
        self._link = None
        self._sent.clear()
        self._jog = (0, 0)
        if self._calib:
            self._calib = None
            self.calibration_changed.emit("")

    def _on_link_state(self, state: LinkState) -> None:
        if state is LinkState.CONNECTED and not self._initialized:
            self._initialized = True
            if self._link is not None and self._link.protocol == 2:
                self._initialize()  # firmware v1 : aucune commande n'est envoyée
        elif state is LinkState.LOST:
            self._jog = (0, 0)
            if self._calib:
                self._abort_calibration("liaison perdue")

    def _on_reboot(self) -> None:
        self.message.emit("error", "La carte a redémarré : origine et réglages perdus. Réinitialisation.")
        self._jog = (0, 0)
        if self._calib:
            self._abort_calibration("redémarrage de la carte")
        self._initialize()

    def _initialize(self) -> None:
        """Réglages envoyés à chaque connexion (la carte redémarre à l'ouverture du port)."""
        self._last_limits = None
        self._send(p.set_mode(manual=True))
        self._send_watchdog()
        self._ensure_limits(self.effective_speed())

    def apply_config(self, config: AppConfig) -> None:
        self.config = config
        self.jog_speed_mm_s = min(self.jog_speed_mm_s, config.limits.speed_max_mm_s)
        self.jog_accel_mm_s2 = min(self.jog_accel_mm_s2, config.limits.accel_max_mm_s2)
        self._last_limits = None
        if self.model.connected:
            self._send_watchdog()
        self.config_changed.emit()

    def _send_watchdog(self) -> None:
        s = self.config.safety
        self._send(p.set_watchdog(s.watchdog_ms if s.watchdog_enabled else 0))

    # ------------------------------------------------------------ envoi

    def _send(self, command: p.Command, urgent: bool = False) -> int | None:
        if self._link is None:
            self.message.emit("error", f"{command} non envoyée : aucune liaison")
            return None
        request_id = self._link.submit(command, urgent=urgent)
        self._sent[request_id] = command
        self.command_status.emit(str(command), "envoyée")
        return request_id

    def _on_result(self, result: CommandResult) -> None:
        self._sent.pop(result.request_id, None)
        text = str(result.command)
        status = result.outcome.value + (f" ({result.detail})" if result.detail else "")
        self.command_status.emit(text, status)
        if result.outcome is Outcome.SENT:
            pass  # ligne v1 : envoyée, aucun accusé possible (affiché dans la barre d'état)
        elif result.outcome is Outcome.CONFIRMED:
            if result.command.code == 113 and result.reply:
                self.model.watchdog_ms = result.reply.values.get("T", 0)
                self.model.changed.emit()
            if result.command.code == 130:
                # posé à la confirmation : l'état reçu juste avant M130 ne montrait aucun mouvement
                self.model.homing_requested = True
                self._homing = True
        else:
            if result.command.code == 121:
                self._last_limits = None
            if result.command.code == 130:
                self.model.homing_requested = False
            level = "warning" if result.outcome in (Outcome.REJECTED, Outcome.CANCELLED) else "error"
            self.message.emit(level, f"{text} {status}")
        if self._calib and result.request_id == self._calib.get("wait_id"):
            if result.outcome is Outcome.CONFIRMED:
                self._calib["confirmed"] = True
            else:
                self._abort_calibration(f"{text} {status}")

    def send(self, command, urgent: bool = False) -> int | None:
        """Envoi direct (ligne de test). Les vérifications sont à la charge de l'appelant."""
        return self._send(command, urgent)

    def _ensure_limits(self, speed_mm_s: float) -> None:
        u = self.config.common_units
        accel = min(self.jog_accel_mm_s2, self.config.limits.accel_max_mm_s2)
        limits = (u.accel_to_fw(accel), u.speed_magnitude_to_fw(speed_mm_s))
        if limits != self._last_limits:
            self._send(p.set_motion_limits(*limits))
            self._last_limits = limits

    # --------------------------------------------------------- intentions

    @property
    def homed(self) -> bool:
        st = self.model.status
        return bool(st and st.homed)

    def effective_speed(self) -> float:
        return min(self.jog_speed_mm_s, speed_cap(self.config, self.homed))

    def _refuse(self, reason: str) -> None:
        self.message.emit("warning", f"Mouvement refusé : {reason}")

    def _check(self, homing: bool = False) -> MachineStatus | None:
        decision = (can_home if homing else can_move)(self.model.state, self.model.status)
        if not decision:
            self._refuse(decision.reason)
            return None
        if self._calib:
            self._refuse("mesure des courses en cours")
            return None
        return self.model.status

    def jog_start(self, sx: int, sy: int) -> None:
        """Jog continu dans la direction (sx, sy) ∈ {-1, 0, 1}²."""
        st = self._check()
        if st is None:
            return
        speed = self.effective_speed()
        self._ensure_limits(speed)
        speeds: dict[str, int] = {}
        targets: dict[str, int] = {}
        for axis, sign, homed, pos in (("X", sx, st.homed_x, st.x), ("Y", sy, st.homed_y, st.y)):
            if sign == 0:
                continue
            units = self.config.axis(axis).units
            bounds = soft_bounds(self.config, axis)
            if homed and bounds:
                lo, hi = bounds
                current = units.steps_to_mm(pos)
                if (sign > 0 and current >= hi) or (sign < 0 and current <= lo):
                    self.message.emit("warning", f"{axis} : limite logicielle atteinte")
                    continue
                targets[axis] = units.mm_to_steps(hi if sign > 0 else lo)
            else:
                speeds[axis] = units.speed_to_fw(sign * speed)
        if targets:
            self._send(p.move_absolute(targets.get("X"), targets.get("Y")))
        if speeds:
            self._send(p.set_speeds(speeds.get("X"), speeds.get("Y")))
        self._jog = (sx if ("X" in targets or "X" in speeds) else 0, sy if ("Y" in targets or "Y" in speeds) else 0)

    def jog_stop(self) -> None:
        sx, sy = self._jog
        self._jog = (0, 0)
        if (sx or sy) and self._link is not None:
            self._send(p.set_speeds(0 if sx else None, 0 if sy else None))

    @property
    def jogging(self) -> bool:
        return self._jog != (0, 0)

    def step(self, dx_mm: float, dy_mm: float) -> None:
        st = self._check()
        if st is None:
            return
        for axis, delta in (("X", dx_mm), ("Y", dy_mm)):
            if delta:
                decision = check_relative(self.config, st, axis, delta)
                if not decision:
                    return self._refuse(decision.reason)
        dx = self.config.x.units.mm_to_steps(dx_mm) if dx_mm else None
        dy = self.config.y.units.mm_to_steps(dy_mm) if dy_mm else None
        if not dx and not dy:
            return self._refuse("incrément inférieur à un micropas")
        self._ensure_limits(self.effective_speed())
        self._send(p.move_relative(dx or None, dy or None))

    def go_to(self, x_mm: float, y_mm: float) -> bool:
        st = self._check()
        if st is None:
            return False
        decision = check_target(self.config, st, x_mm, y_mm)
        if not decision:
            self._refuse(decision.reason)
            return False
        self._ensure_limits(self.effective_speed())
        self._send(p.move_absolute(self.config.x.units.mm_to_steps(x_mm), self.config.y.units.mm_to_steps(y_mm)))
        return True

    def home(self) -> None:
        if self._check(homing=True) is None:
            return
        f = self.config.common_units.speed_magnitude_to_fw(self.config.manual.home_speed_mm_s)
        self._send(p.home(x=True, y=True, speed=f))

    def stop(self) -> None:
        """Arrêt logiciel : prioritaire, annule les mouvements en attente."""
        self._jog = (0, 0)
        if self._calib:
            self._calib = None
            self.calibration_changed.emit("")
            self.message.emit("warning", "Mesure des courses interrompue par l'arrêt")
        self.model.homing_requested = False
        self._homing = False
        if self._link is None or self._link.protocol == 1:
            return  # firmware v1 : l'application n'a lancé aucun mouvement
        self._send(p.stop_all(), urgent=True)

    def clear_alarms(self) -> None:
        self._send(p.clear_alarms())

    # ------------------------------------------------- mesure des courses

    def start_calibration(self) -> None:
        st = self._check(homing=True)
        if st is None:
            return
        if not st.homed:
            return self._refuse("faites d'abord la prise d'origine")
        self._calib = {"axes": ["X", "Y"], "index": 0, "results": {}}
        self._calibration_approach()

    def _calibration_approach(self) -> None:
        axis = self._calib["axes"][self._calib["index"]]
        speed = self.config.manual.calibration_speed_mm_s
        units = self.config.axis(axis).units
        self._ensure_limits(speed)
        cmd = p.set_speeds(**{"vx" if axis == "X" else "vy": units.speed_to_fw(speed)})
        self._calib.update(phase="approach", t0=time.monotonic(), confirmed=False, wait_id=self._send(cmd))
        self.calibration_changed.emit(f"Mesure de la course {axis} : avance lente vers {axis}max…")

    def on_status(self, st: MachineStatus) -> None:
        if self._homing and not st.moving:
            self._homing = False
            if st.homed:
                self.message.emit("info", "Prise d'origine terminée : position référencée sur Xmin, Ymin")
            else:
                self.message.emit("error", "Prise d'origine interrompue : position non référencée")
        c = self._calib
        if not c:
            return
        if st.blocking_alarm:
            return self._abort_calibration("alarme bloquante")
        if time.monotonic() - c["t0"] > CALIBRATION_TIMEOUT_S:
            return self._abort_calibration("délai dépassé")
        if not c["confirmed"]:
            return
        axis = c["axes"][c["index"]]
        moving = st.moving_x if axis == "X" else st.moving_y
        at_max = st.endstops.x_max if axis == "X" else st.endstops.y_max
        units = self.config.axis(axis).units
        if c["phase"] == "approach" and at_max and not moving:
            travel = units.steps_to_mm(st.x if axis == "X" else st.y)
            c["results"][axis] = travel
            self.message.emit("info", f"Course {axis} mesurée : {travel:.2f} mm")
            self._send(p.clear_alarms())  # bit « fin de course touchée » attendu ici
            self._ensure_limits(self.effective_speed())
            back = units.mm_to_steps(self.config.limits.soft_margin_mm)
            cmd = p.move_absolute(**{"x" if axis == "X" else "y": back})
            c.update(phase="return", confirmed=False, wait_id=self._send(cmd))
            self.calibration_changed.emit(f"Course {axis} : {travel:.2f} mm. Retour vers l'origine…")
        elif c["phase"] == "return" and not moving:
            c["index"] += 1
            if c["index"] < len(c["axes"]):
                self._calibration_approach()
            else:
                self._finish_calibration()

    def _finish_calibration(self) -> None:
        results = self._calib["results"]
        self._calib = None
        for axis, travel in results.items():
            self.config.axis(axis).travel_mm = round(travel, 3)
        try:
            path = save_config(self.config)
            self.message.emit("info", f"Courses enregistrées dans {path}")
        except (OSError, ValueError) as exc:
            self.message.emit("error", f"Courses mesurées mais non enregistrées : {exc}")
        self.calibration_changed.emit("")
        self.config_changed.emit()

    def _abort_calibration(self, reason: str) -> None:
        self._calib = None
        if self._link is not None:
            self._send(p.stop_all(), urgent=True)
        self.calibration_changed.emit("")
        self.message.emit("error", f"Mesure des courses interrompue : {reason}")

    @property
    def calibrating(self) -> bool:
        return self._calib is not None
