"""
Pont de communication série (Serial Bridge) pour la brodeuse numérique.
Permet d'envoyer des commandes de déplacement et de synchronisation G-code
à la carte MKS Base V1.4 (ATmega2560) via liaison USB.
"""

import time
import serial
import serial.tools.list_ports


class EmbroiderySerialBridge:
    def __init__(self, port: str = None, baudrate: int = 115200, timeout: float = 2.0):
        self.port = port or self.detect_port()
        self.baudrate = baudrate
        self.timeout = timeout
        self.connection = None

    @staticmethod
    def detect_port() -> str:
        """Détecte automatiquement le premier port série disponible (USB)."""
        ports = serial.tools.list_ports.comports()
        for p in ports:
            if "USB" in p.device or "ACM" in p.device:
                return p.device
        return "/dev/ttyUSB0"

    def connect(self) -> bool:
        """Établit la connexion avec la carte de commande."""
        try:
            self.connection = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            time.sleep(2.0)  # Attente de réinitialisation de l'ATmega au reset DTR
            self.connection.reset_input_buffer()
            print(f"[SerialBridge] Connecté sur {self.port} à {self.baudrate} bauds.")
            return True
        except serial.SerialException as err:
            print(f"[SerialBridge] Erreur de connexion sur {self.port}: {err}")
            return False

    def send_command(self, cmd: str) -> str:
        """Envoie une ligne de commande et attend l'acquittement 'ok'."""
        if not self.connection or not self.connection.is_open:
            raise RuntimeError("Port série non ouvert.")
        
        cmd_clean = cmd.strip() + "\n"
        self.connection.write(cmd_clean.encode("utf-8"))
        
        # Attente de la réponse
        response = self.connection.readline().decode("utf-8", errors="ignore").strip()
        return response

    def close(self):
        """Ferme la liaison série proprement."""
        if self.connection and self.connection.is_open:
            self.connection.close()
            print("[SerialBridge] Connexion série fermée.")


if __name__ == "__main__":
    bridge = EmbroiderySerialBridge()
    if bridge.connect():
        # Test d'interrogation initiale
        print("[Test] Envoi de ping...")
        resp = bridge.send_command("M115")
        print(f"[Test] Réponse reçue: {resp}")
        bridge.close()
