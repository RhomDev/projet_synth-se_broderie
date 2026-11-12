"""Règles de sécurité appliquées avant tout envoi de mouvement.

Fonctions pures : elles décident, sans rien envoyer. Le firmware garde ses propres
protections (fins de course, chien de garde) ; ces règles s'y ajoutent.
"""
from __future__ import annotations

from dataclasses import dataclass

from communication.protocol import MachineStatus

from .config import AppConfig
from .state import MachineState


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str = ""

    def __bool__(self) -> bool:
        return self.allowed


ALLOWED = Decision(True)

_REFUSAL = {
    MachineState.DISCONNECTED: "carte non connectée",
    MachineState.CONNECTING: "connexion en cours",
    MachineState.LOST: "liaison perdue",
    MachineState.STALE: "état de la machine inconnu (données trop anciennes)",
    MachineState.ALARM: "alarme active : acquittez-la d'abord",
    MachineState.HOMING: "prise d'origine en cours",
    MachineState.V1_DIAGNOSTIC: "firmware v1 : déplacements désactivés (ni accusé ni chien de garde), "
                                "flashez le firmware v2",
    MachineState.EMBROIDERY: "carte en mode broderie (pas émis seulement fenêtre ouverte)",
}


def can_move(state: MachineState, status: MachineStatus | None) -> Decision:
    """Un ordre de mouvement est-il envisageable dans cet état ?"""
    if state in _REFUSAL:
        return Decision(False, _REFUSAL[state])
    if status is None:
        return Decision(False, "état de la machine inconnu")
    if not status.manual_mode:
        return Decision(False, "la carte n'est pas en mode manuel")
    return ALLOWED


def can_home(state: MachineState, status: MachineStatus | None) -> Decision:
    decision = can_move(state, status)
    if decision and state is MachineState.MOVING:
        return Decision(False, "attendez la fin du mouvement")
    return decision


def speed_cap(cfg: AppConfig, homed: bool) -> float:
    """Vitesse manuelle maximale (mm/s) : réduite tant que l'origine n'est pas faite."""
    cap = cfg.limits.speed_max_mm_s
    return cap if homed else min(cap, cfg.limits.pre_home_speed_max_mm_s)


def soft_bounds(cfg: AppConfig, axis: str) -> tuple[float, float] | None:
    """Plage autorisée (mm) d'un axe référencé, ou None si la course est inconnue."""
    travel = cfg.axis(axis).travel_mm
    if travel is None:
        return None
    m = cfg.limits.soft_margin_mm
    return (m, travel - m)


def check_target(cfg: AppConfig, status: MachineStatus | None, x_mm: float, y_mm: float) -> Decision:
    """Cible absolue (clic sur le plateau ou saisie)."""
    if status is None:
        return Decision(False, "état de la machine inconnu")
    if not (status.homed_x and status.homed_y):
        return Decision(False, "prise d'origine non faite")
    for axis, value in (("X", x_mm), ("Y", y_mm)):
        bounds = soft_bounds(cfg, axis)
        if bounds is None:
            return Decision(False, f"course {axis} inconnue : mesurez-la ou saisissez-la")
        lo, hi = bounds
        if not lo <= value <= hi:
            return Decision(False, f"{axis} = {value:.2f} mm hors limites ({lo:.2f} à {hi:.2f} mm)")
    for zone in cfg.view.forbidden_zones:
        if zone.contains(x_mm, y_mm):
            return Decision(False, f"cible dans la zone interdite « {zone.name} »")
    return ALLOWED


def check_relative(cfg: AppConfig, status: MachineStatus | None, axis: str, delta_mm: float) -> Decision:
    """Incrément sur un axe. Avant l'origine, seules les fins de course protègent."""
    if status is None:
        return Decision(False, "état de la machine inconnu")
    homed = status.homed_x if axis == "X" else status.homed_y
    bounds = soft_bounds(cfg, axis)
    if not homed or bounds is None:
        return ALLOWED
    current = cfg.axis(axis).units.steps_to_mm(status.x if axis == "X" else status.y)
    target = current + delta_mm
    lo, hi = bounds
    if not lo <= target <= hi:
        return Decision(False, f"{axis} irait à {target:.2f} mm, hors limites ({lo:.2f} à {hi:.2f} mm)")
    return ALLOWED
