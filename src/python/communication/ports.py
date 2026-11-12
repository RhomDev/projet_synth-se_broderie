"""Détection de la carte MKS Base par son identifiant USB (Ubuntu et Windows).

On cherche la puce FTDI FT232R (VID:PID 0403:6001) plutôt qu'un nom de port :
``/dev/ttyUSB0`` sous Linux, ``COMx`` sous Windows. Lister les ports ne les ouvre
pas, donc ne redémarre pas la carte.
"""
from __future__ import annotations

from dataclasses import dataclass

BOARD_VID = 0x0403
BOARD_PID = 0x6001


@dataclass(frozen=True)
class BoardPort:
    device: str
    description: str
    serial_number: str | None

    def __str__(self) -> str:
        sn = f", n° {self.serial_number}" if self.serial_number else ""
        return f"{self.device} ({self.description}{sn})"


def find_board_ports() -> list[BoardPort]:
    """Ports série dont le VID:PID correspond à la carte. Liste vide si pyserial manque."""
    try:
        from serial.tools import list_ports
    except ImportError:
        return []
    found = []
    for p in list_ports.comports():
        if p.vid == BOARD_VID and p.pid == BOARD_PID:
            found.append(BoardPort(p.device, p.description or "FT232R", p.serial_number))
    return sorted(found, key=lambda b: b.device)
