"""Modèle de mouvement d'un axe du plateau XY (moteur pas à pas + poulie-courroie).

Ce module remplace le tableur ``calcul_stepper_moteur.xlsx``. Il répond à trois questions :

1. Quelle accélération ``a_max`` et quelle vitesse ``v_max`` l'axe peut-il tenir, selon la charge ?
2. Quel profil de vitesse (triangle ou trapèze) faut-il pour parcourir un déplacement donné ?
3. Quelle est la plus longue distance parcourue dans la fenêtre d'avance de l'aiguille ?

Les formules sont démontrées dans le document « Accélération maximale du moteur 17HS4401 ».
Les frottements sont négligés par défaut (``friction_coeff = 0``) : ils pèsent environ 1 % du couple.

Unités : SI partout (m, s, kg, N·m, A, V, ohm, H), sauf mention contraire.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Literal

G = 9.81  # pesanteur, m/s²
_EPS = 1e-9


# --------------------------------------------------------------------------- données


@dataclass(frozen=True)
class Motor:
    """Caractéristiques d'un moteur pas à pas (valeurs du datasheet)."""

    name: str
    holding_torque: float  # couple de maintien, N·m
    rated_current: float  # courant nominal par phase, A
    resistance: float  # résistance de phase, ohm
    inductance: float  # inductance de phase, H
    rotor_inertia: float  # inertie du rotor, kg·m²
    steps_per_rev: int = 200  # pas entiers par tour (1,8°)


# MotionKing 17HS4401 : 40 N·cm, 1,7 A, 1,5 ohm, 2,8 mH, 54 g·cm².
MOTOR_17HS4401 = Motor(
    name="17HS4401",
    holding_torque=0.40,
    rated_current=1.7,
    resistance=1.5,
    inductance=2.8e-3,
    rotor_inertia=54e-7,
    steps_per_rev=200,
)


def pulley_radius(teeth: int, pitch: float = 2e-3) -> float:
    """Rayon primitif d'une poulie crantée. GT2 de 20 dents : 6,37 mm."""
    return teeth * pitch / (2 * math.pi)


# Poulie GT2 de 20 dents (pas 2 mm, 40 mm/tour) : rayon 6,37 mm. Confirmée pour le projet.
GT2_20T_RADIUS = pulley_radius(20)


@dataclass(frozen=True)
class Axis:
    """Un axe : moteur + poulie + masse déplacée + alimentation + marges."""

    motor: Motor = MOTOR_17HS4401
    supply_voltage: float = 12.0  # tension d'alimentation du driver, V
    pulley_radius: float = GT2_20T_RADIUS  # rayon de la poulie, m (GT2 20 dents)
    moving_mass: float = 0.0  # masse déplacée par l'axe, kg ; 0 = rotor seul, en attendant la mesure
    friction_coeff: float = 0.0  # μ ; 0 = frottements négligés
    safety_factor: float = 0.5  # part du couple maximal réellement utilisée
    speed_factor: float = 1.0  # part de la vitesse du coude retenue (0,7 à 1)
    microstep: int = 16  # micropas par pas entier (A4982 : MS1 = MS2 = HIGH)

    def __post_init__(self) -> None:
        for name in ("supply_voltage", "pulley_radius", "safety_factor", "speed_factor"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} doit être strictement positif")
        if self.moving_mass < 0:
            raise ValueError("moving_mass doit être positif ou nul")
        if self.friction_coeff < 0:
            raise ValueError("friction_coeff doit être positif ou nul")
        if self.microstep < 1:
            raise ValueError("microstep doit être >= 1")

    # ------------------------------------------------------------- couple et accélération

    @property
    def usable_torque(self) -> float:
        """Couple utilisable C_dispo (N·m) : couple de maintien × coefficient de sécurité.

        Valable jusqu'à la vitesse du coude (couple plein)."""
        return self.safety_factor * self.motor.holding_torque

    @property
    def effective_inertia_per_r(self) -> float:
        """Dénominateur J_rotor / r + m × r (kg·m)."""
        return self.motor.rotor_inertia / self.pulley_radius + self.moving_mass * self.pulley_radius

    @property
    def a_max(self) -> float:
        """Accélération maximale (m/s²) : (C_dispo − μ m g r) / (J_rotor / r + m r)."""
        torque = self.usable_torque - self.friction_coeff * self.moving_mass * G * self.pulley_radius
        return max(0.0, torque / self.effective_inertia_per_r)

    # ------------------------------------------------------------------------- vitesse

    @property
    def corner_speed_rev(self) -> float:
        """Vitesse du coude en tours/s : V / (2 L I spr). Au-delà, le couple baisse."""
        m = self.motor
        return self.supply_voltage / (2 * m.inductance * m.rated_current * m.steps_per_rev)

    @property
    def corner_speed(self) -> float:
        """Vitesse linéaire du coude (m/s) : tours/s × 2π r."""
        return self.corner_speed_rev * 2 * math.pi * self.pulley_radius

    @property
    def v_max(self) -> float:
        """Vitesse maximale retenue pour la planification (m/s)."""
        return self.speed_factor * self.corner_speed

    # --------------------------------------------------------- conversions pour le firmware

    @property
    def microsteps_per_m(self) -> float:
        """Micropas par mètre de déplacement."""
        return self.motor.steps_per_rev * self.microstep / (2 * math.pi * self.pulley_radius)

    @property
    def microstep_length(self) -> float:
        """Longueur d'un micropas (m)."""
        return 1.0 / self.microsteps_per_m

    def to_microsteps(self, value: float) -> float:
        """Convertit une distance (m), une vitesse (m/s) ou une accélération (m/s²) en
        micropas, micropas/s ou micropas/s²."""
        return value * self.microsteps_per_m

    def step_rate(self, speed: float) -> float:
        """Cadence des impulsions STEP (micropas/s) à une vitesse donnée."""
        return self.to_microsteps(speed)


# ----------------------------------------------------------------------------- profils

Kind = Literal["none", "triangle", "trapezoid"]


@dataclass(frozen=True)
class MovePlan:
    """Profil de vitesse d'un déplacement (démarrage et arrêt à vitesse nulle)."""

    distance: float  # m
    duration: float  # durée du profil, s
    kind: Kind
    accel: float  # accélération utilisée, m/s²
    v_peak: float  # vitesse de pointe, m/s
    t_accel: float  # durée de la phase d'accélération (= celle de décélération), s
    t_cruise: float  # durée du palier à vitesse constante, s
    feasible: bool
    reason: str = ""


def plan_fastest(distance: float, a_max: float, v_max: float) -> MovePlan:
    """Profil le plus rapide : triangle si v_max n'est pas atteinte, sinon trapèze.

    Le triangle est le cas limite du trapèze (palier de durée nulle), donc un seul
    algorithme couvre tous les déplacements."""
    if a_max <= 0 or v_max <= 0:
        raise ValueError("a_max et v_max doivent être strictement positifs")
    d = abs(distance)
    if d == 0:
        return MovePlan(0.0, 0.0, "none", 0.0, 0.0, 0.0, 0.0, True)
    if d <= v_max**2 / a_max:  # v_max jamais atteinte
        t1 = math.sqrt(d / a_max)
        return MovePlan(d, 2 * t1, "triangle", a_max, a_max * t1, t1, 0.0, True)
    t1 = v_max / a_max
    t_cruise = d / v_max - t1
    return MovePlan(d, 2 * t1 + t_cruise, "trapezoid", a_max, v_max, t1, t_cruise, True)


def plan_in_window(distance: float, window: float, a_max: float, v_max: float) -> MovePlan:
    """Profil le plus doux qui finit exactement à la fin de la fenêtre.

    La durée est imposée par la machine (angle de l'arbre principal) : on utilise toute
    la fenêtre avec l'accélération minimale, ce qui limite vibrations et risque de décrochage.
    Si même le profil le plus rapide dépasse la fenêtre, ``feasible`` vaut False et le plan
    renvoyé est le plus rapide possible."""
    if window <= 0:
        raise ValueError("window doit être strictement positif")
    d = abs(distance)
    fastest = plan_fastest(d, a_max, v_max)
    if d == 0:
        return fastest
    if fastest.duration > window * (1 + _EPS):
        reason = f"durée mini {fastest.duration * 1e3:.1f} ms > fenêtre {window * 1e3:.1f} ms"
        return MovePlan(d, fastest.duration, fastest.kind, fastest.accel, fastest.v_peak,
                        fastest.t_accel, fastest.t_cruise, False, reason)
    if 2 * d / window <= v_max:  # triangle : accélère t/2, décélère t/2
        return MovePlan(d, window, "triangle", 4 * d / window**2, 2 * d / window,
                        window / 2, 0.0, True)
    t1 = window - d / v_max  # trapèze à v_max, accélération minimale
    return MovePlan(d, window, "trapezoid", v_max / t1, v_max, t1, window - 2 * t1, True)


def max_distance(window: float, a_max: float, v_max: float) -> float:
    """Plus grande distance parcourue (départ et arrivée à l'arrêt) dans la fenêtre.

    Triangle si v_max / a_max >= window / 2 : a t² / 4.  Sinon trapèze : a t1² + v (t − 2 t1)."""
    t1 = v_max / a_max
    if t1 >= window / 2:
        return a_max * window**2 / 4
    return a_max * t1**2 + v_max * (window - 2 * t1)


def required_accel(distance: float, window: float) -> float:
    """Accélération du profil triangle qui parcourt ``distance`` en ``window`` : 4 Δ / t²."""
    return 4 * abs(distance) / window**2


# --------------------------------------------------------------------------- synthèse


def capability_table(axis: Axis, masses: list[float], window: float) -> list[dict]:
    """Pour chaque masse : a_max, profil, vitesse de pointe, distance max dans la fenêtre."""
    rows = []
    for m in masses:
        ax = replace(axis, moving_mass=m)
        a, v = ax.a_max, ax.v_max
        if a <= 0:  # le frottement dépasse le couple disponible : l'axe ne démarre pas
            rows.append({"masse_kg": m, "a_max_m_s2": 0.0, "profil": "none", "v_pic_m_s": 0.0, "x_max_mm": 0.0})
            continue
        x = max_distance(window, a, v)
        rows.append({
            "masse_kg": m,
            "a_max_m_s2": a,
            "profil": "triangle" if v / a >= window / 2 else "trapezoid",
            "v_pic_m_s": min(v, a * window / 2),
            "x_max_mm": x * 1e3,
        })
    return rows


def _main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="Capacités d'un axe du plateau XY")
    p.add_argument("--masse", type=float, default=0.0, help="masse déplacée, kg")
    p.add_argument("--rayon", type=float, default=GT2_20T_RADIUS, help="rayon de poulie, m")
    p.add_argument("--tension", type=float, default=12.0, help="alimentation, V")
    p.add_argument("--fenetre", type=float, default=0.04, help="fenêtre d'avance, s")
    args = p.parse_args()

    ax = Axis(supply_voltage=args.tension, pulley_radius=args.rayon, moving_mass=args.masse)
    print(f"Moteur {ax.motor.name}, {ax.supply_voltage:g} V, r = {ax.pulley_radius * 1e3:.2f} mm, m = {ax.moving_mass:g} kg")
    print(f"  C_dispo  = {ax.usable_torque * 100:.1f} N·cm")
    print(f"  v_max    = {ax.v_max * 1e3:.0f} mm/s ({ax.step_rate(ax.v_max):.0f} micropas/s)")
    print(f"  a_max    = {ax.a_max:.1f} m/s² ({ax.to_microsteps(ax.a_max):.3g} micropas/s²)")
    print(f"  x_max    = {max_distance(args.fenetre, ax.a_max, ax.v_max) * 1e3:.1f} mm en {args.fenetre * 1e3:.0f} ms")
    print("\n masse (kg) | a_max (m/s²) | profil    | x_max (mm)")
    for r in capability_table(ax, [0, 0.25, 0.5, 1, 2, 3], args.fenetre):
        print(f" {r['masse_kg']:10g} | {r['a_max_m_s2']:12.1f} | {r['profil']:9s} | {r['x_max_mm']:.1f}")


if __name__ == "__main__":
    
    _main()
