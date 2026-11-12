"""Ligne de test : piquer une ligne droite, premier essai de broderie.

Principe, avec les seules commandes déjà validées :
1. la carte passe en mode broderie (``M112 S0``) : les pas ne sortent que pendant
   la fenêtre aiguille (aiguille hors du tissu, capteurs TCST2300) ;
2. une consigne de vitesse v1 constante (ligne ``X… Y…``) fait avancer le cadre de
   v × T à chaque fenêtre de durée T : c'est la longueur de point ;
3. le PC suit la position (``M111``) et coupe la consigne en fin de ligne, puis
   remet la carte en mode manuel.

Limites connues :
- la longueur de point suit la durée de la fenêtre, donc la vitesse de couture :
  coudre à vitesse régulière ;
- la consigne v1 n'a pas de rampe : le cadre démarre et s'arrête net à chaque
  fenêtre, d'où une vitesse plafonnée (paramètre ``line_speed_max_mm_s``) ;
- fin de ligne précise à environ un point près (interrogation à 20 Hz).
Une commande « un point par fenêtre » côté firmware lèverait ces limites ; elle
reste à proposer et à valider.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal

from communication import protocol as p
from communication.protocol import MachineStatus

from .config import AppConfig
from .safety import Decision, can_move, check_target
from .state import MachineModel

STOP_LATENCY_S = 0.03  # anticipation de l'arrêt (≈ délai moyen entre deux lectures d'état)


@dataclass(frozen=True)
class LinePlan:
    x0: float
    y0: float
    length_mm: float
    angle_deg: float
    stitch_mm: float
    window_s: float
    vx_fw: int
    vy_fw: int

    @property
    def ux(self) -> float:
        return math.cos(math.radians(self.angle_deg))

    @property
    def uy(self) -> float:
        return math.sin(math.radians(self.angle_deg))

    @property
    def x1(self) -> float:
        return self.x0 + self.length_mm * self.ux

    @property
    def y1(self) -> float:
        return self.y0 + self.length_mm * self.uy

    @property
    def speed_mm_s(self) -> float:
        return self.stitch_mm / self.window_s

    @property
    def stitches(self) -> int:
        return max(1, round(self.length_mm / self.stitch_mm))


def plan_line(cfg: AppConfig, status: MachineStatus | None, length_mm: float, angle_deg: float,
              stitch_mm: float, window_s: float) -> tuple[LinePlan | None, Decision]:
    """Calcule la ligne depuis la position actuelle ; refuse si elle sort des limites."""
    if status is None:
        return None, Decision(False, "état de la machine inconnu")
    if not status.homed:
        return None, Decision(False, "faites d'abord la prise d'origine")
    if length_mm <= 0 or stitch_mm <= 0:
        return None, Decision(False, "longueur et longueur de point doivent être > 0")
    if window_s <= 0:
        return None, Decision(False, "durée de fenêtre inconnue : faites tourner la machine ou saisissez-la")
    x0 = cfg.x.units.steps_to_mm(status.x)
    y0 = cfg.y.units.steps_to_mm(status.y)
    ux, uy = math.cos(math.radians(angle_deg)), math.sin(math.radians(angle_deg))
    speed = stitch_mm / window_s
    vmax = cfg.embroidery.line_speed_max_mm_s
    if speed > vmax:
        return None, Decision(False, f"vitesse du cadre {speed:.1f} mm/s > {vmax:g} mm/s autorisés sans rampe : "
                                     "raccourcissez le point ou cousez plus lentement")
    vx = cfg.x.units.speed_to_fw(speed * ux)
    vy = cfg.y.units.speed_to_fw(speed * uy)
    if vx == 0 and vy == 0:
        return None, Decision(False, "vitesse trop faible pour le firmware")
    plan = LinePlan(x0, y0, length_mm, angle_deg, stitch_mm, window_s, vx, vy)
    target = check_target(cfg, status, plan.x1, plan.y1)
    if not target:
        return None, Decision(False, f"fin de ligne : {target.reason}")
    return plan, Decision(True)


class LineTest(QObject):
    progress = Signal(str)
    finished = Signal(str, str)  # niveau, message
    running_changed = Signal(bool)
    trace_point = Signal(float, float)

    def __init__(self, motion, model: MachineModel, parent=None) -> None:
        super().__init__(parent)
        self.motion = motion
        self.model = model
        self.plan: LinePlan | None = None
        self._phase = ""  # "" | running | finishing
        self._done_mm = 0.0

    @property
    def running(self) -> bool:
        return bool(self._phase)

    def start(self, plan: LinePlan) -> bool:
        decision = can_move(self.model.state, self.model.status)
        if not decision:
            self.finished.emit("warning", f"Ligne refusée : {decision.reason}")
            return False
        if self.motion.calibrating or self.motion.jogging:
            self.finished.emit("warning", "Ligne refusée : un autre mouvement est en cours")
            return False
        self.plan = plan
        self._phase = "running"
        self._done_mm = 0.0
        self.motion.send(p.set_mode(manual=False))
        self.motion.send(p.LegacySpeeds(plan.vx_fw, plan.vy_fw))
        self.running_changed.emit(True)
        self.progress.emit("Ligne armée : lancez la machine à coudre. Le cadre n'avance que fenêtre ouverte.")
        return True

    def abort(self, reason: str) -> None:
        if not self._phase:
            return
        self._end("error", f"Ligne interrompue : {reason}")

    def on_status(self, st: MachineStatus) -> None:
        if not self._phase or self.plan is None:
            return
        plan = self.plan
        cfg = self.motion.config
        x = cfg.x.units.steps_to_mm(st.x)
        y = cfg.y.units.steps_to_mm(st.y)
        self.trace_point.emit(x, y)
        done = (x - plan.x0) * plan.ux + (y - plan.y0) * plan.uy
        self._done_mm = done
        if self._phase == "finishing":
            if not st.moving:
                lateral = abs(-(x - plan.x0) * plan.uy + (y - plan.y0) * plan.ux)
                self._finish_report(done, lateral, st)
            return
        if st.blocking_alarm:
            return self._end("error", "Ligne interrompue : alarme bloquante")
        es = st.endstops
        if (plan.vx_fw > 0 and es.x_max) or (plan.vx_fw < 0 and es.x_min) or \
           (plan.vy_fw > 0 and es.y_max) or (plan.vy_fw < 0 and es.y_min):
            return self._end("error", "Ligne interrompue : fin de course atteinte")
        remaining = plan.length_mm - done
        window = f"{st.window_us / 1000:.1f} ms" if st.window_us else "non mesurée"
        self.progress.emit(f"{max(done, 0):.1f} / {plan.length_mm:.1f} mm · fenêtre {window}")
        if remaining <= plan.speed_mm_s * STOP_LATENCY_S:
            self._stop_motion()
            self._phase = "finishing"

    def _stop_motion(self) -> None:
        self.motion.send(p.LegacySpeeds(0, 0))
        self.motion.send(p.set_mode(manual=True))

    def _end(self, level: str, text: str) -> None:
        self._stop_motion()
        self._phase = ""
        self.running_changed.emit(False)
        self.finished.emit(level, text)

    def _finish_report(self, done: float, lateral: float, st: MachineStatus) -> None:
        plan = self.plan
        self._phase = ""
        self.running_changed.emit(False)
        window = f", dernière fenêtre {st.window_us / 1000:.1f} ms" if st.window_us else ""
        self.finished.emit(
            "info",
            f"Ligne terminée : {done:.2f} mm réalisés sur {plan.length_mm:.2f} mm visés "
            f"(écart latéral {lateral:.2f} mm), point visé {plan.stitch_mm:g} mm{window}.")

    def notify_stopped(self) -> None:
        """Appelé par l'ARRÊT logiciel : la ligne est abandonnée, mode manuel rétabli."""
        if self._phase:
            self.motion.send(p.set_mode(manual=True))
            self._phase = ""
            self.running_changed.emit(False)
            self.finished.emit("warning", f"Ligne arrêtée à {self._done_mm:.1f} mm")
