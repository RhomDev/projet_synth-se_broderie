"""Conversions mm ↔ micropas ↔ unités du firmware.

Sens des axes : le positif s'éloigne de la fin de course min (Xmin à gauche,
Ymin en bas). C'est imposé par le firmware, qui associe DIR=1 aux fins de course
max ; il n'y a donc pas d'option d'inversion.
"""
from __future__ import annotations

from dataclasses import dataclass

from communication.protocol import ACCEL_MAX, SPEED_MAX, SPEED_SCALE, TICK_HZ


def steps_per_s_to_fw(steps_per_s: float) -> float:
    return steps_per_s * SPEED_SCALE / TICK_HZ


def fw_to_steps_per_s(fw: float) -> float:
    return fw * TICK_HZ / SPEED_SCALE


def _clamp(value: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, value))


@dataclass(frozen=True)
class AxisUnits:
    steps_per_mm: float

    def __post_init__(self) -> None:
        if self.steps_per_mm <= 0:
            raise ValueError("steps_per_mm doit être strictement positif")

    def mm_to_steps(self, mm: float) -> int:
        return int(round(mm * self.steps_per_mm))

    def steps_to_mm(self, steps: float) -> float:
        return steps / self.steps_per_mm

    def speed_to_fw(self, mm_s: float) -> int:
        """Vitesse signée (mm/s) → consigne firmware, bornée à ±32 768."""
        return _clamp(int(round(steps_per_s_to_fw(mm_s * self.steps_per_mm))), -SPEED_MAX, SPEED_MAX)

    def speed_magnitude_to_fw(self, mm_s: float) -> int:
        """Vitesse maximale (mm/s) → paramètre V/F, borné à 1..32 768."""
        return _clamp(int(round(steps_per_s_to_fw(abs(mm_s) * self.steps_per_mm))), 1, SPEED_MAX)

    def fw_to_speed(self, fw: float) -> float:
        return fw_to_steps_per_s(fw) / self.steps_per_mm

    def accel_to_fw(self, mm_s2: float) -> int:
        """Accélération (mm/s²) → paramètre A (µpas/s²), borné à 1..16 000 000."""
        return _clamp(int(round(abs(mm_s2) * self.steps_per_mm)), 1, ACCEL_MAX)

    @property
    def max_speed_mm_s(self) -> float:
        """Vitesse maximale que le firmware sait produire (25 000 µpas/s)."""
        return self.fw_to_speed(SPEED_MAX)
