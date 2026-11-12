"""Transport série réel (pyserial) vers la carte MKS Base.

Attention : ouvrir le port redémarre l'ATmega (signal DTR de la puce FTDI). Les
vitesses repartent à 0 et l'origine est perdue ; on attend la fin du chargeur
d'amorçage avant d'envoyer quoi que ce soit.
"""
from __future__ import annotations

import time

BAUDRATE = 1_000_000
BOOT_DELAY_S = 2.0  # chargeur d'amorçage de l'ATmega2560 après le reset DTR
READ_SLICE_S = 0.01


class SerialTransport:
    is_simulation = False

    def __init__(self, port: str, baudrate: int = BAUDRATE, boot_delay: float = BOOT_DELAY_S) -> None:
        self.port = port
        self.baudrate = baudrate
        self.boot_delay = boot_delay
        self.description = f"carte réelle sur {port} ({baudrate} bauds)"
        self._ser = None

    def open(self) -> None:
        import serial  # importé ici : l'application reste utilisable en simulation sans pyserial

        self._ser = serial.Serial(self.port, self.baudrate, timeout=READ_SLICE_S, write_timeout=0.5)
        time.sleep(self.boot_delay)
        self._ser.reset_input_buffer()

    def close(self) -> None:
        if self._ser is not None and self._ser.is_open:
            self._ser.close()
        self._ser = None

    def write(self, data: bytes) -> None:
        if self._ser is None:
            raise OSError("port fermé")
        self._ser.write(data)

    def read(self, timeout: float) -> bytes:
        """Renvoie les octets disponibles ; attend au plus ``timeout`` qu'il en arrive un."""
        if self._ser is None:
            raise OSError("port fermé")
        deadline = time.monotonic() + timeout
        while True:
            waiting = self._ser.in_waiting
            if waiting:
                return self._ser.read(waiting)
            if time.monotonic() >= deadline:
                return b""
            first = self._ser.read(1)  # attend au plus READ_SLICE_S
            if first:
                return first + self._ser.read(self._ser.in_waiting)
