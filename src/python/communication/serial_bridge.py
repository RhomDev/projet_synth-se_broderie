"""
Pont de communication série (Serial Bridge) pour la brodeuse numérique.
Permet d'envoyer des commandes de déplacement et de synchronisation G-code
à la carte MKS Base V1.4 (ATmega2560) via liaison USB.
"""

import time
import serial
import serial.tools.list_ports
import struct


class EmbroiderySerialBridge:
    def __init__(self, port: str = None, baudrate: int = 1000000, timeout: float = 2.0):
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
        """
        Envoie une ligne de commande TEXTE (ex: G-code) et attend l'acquittement 'ok'.
        Ne pas utiliser pour la requête rapide en binaire.
        """
        if not self.connection or not self.connection.is_open:
            raise RuntimeError("Port série non ouvert.")

        cmd_clean = cmd.strip() + "\n"
        self.connection.write(cmd_clean.encode("utf-8"))

        # Attente de la réponse (bloquant jusqu'au \n ou timeout)
        response = self.connection.readline().decode("utf-8", errors="ignore").strip()
        return response

    def request_fast_data(self) -> int:
        """
        NOUVELLE MÉTHODE : Demande la donnée uint16_t en binaire pur.
        Envoie un seul octet 'R' et lit exactement 2 octets en réponse.
        """
        if not self.connection or not self.connection.is_open:
            raise RuntimeError("Port série non ouvert.")

        # 1. Envoi de la commande : 1 seul octet en binaire, pas de \n
        self.connection.write(b'R')

        # 2. Lecture stricte de 2 octets (la taille d'un uint16_t)
        # On utilise read(2) au lieu de readline() car il n'y a pas de \n
        raw_bytes = self.connection.read(2)

        if len(raw_bytes) != 2:
            raise TimeoutError(f"Délai d'attente dépassé. Reçu {len(raw_bytes)} octets sur 2.")

        # 3. Conversion des 2 octets en entier non signé (uint16_t)
        # '<H' = Little-Endian (le standard de l'ATmega), Unsigned Short (16 bits)
        valeur = struct.unpack('<H', raw_bytes)[0]
        return valeur

    def close(self):
        """Ferme la liaison série proprement."""
        if self.connection and self.connection.is_open:
            self.connection.close()
            print("[SerialBridge] Connexion série fermée.")

    def get_v_autorise(self) -> int:
        """Demande la vitesse via M100 et lit la réponse binaire."""
        # On envoie la commande texte avec un retour à la ligne pour déclencher l'exécution
        self.connection.write(b"M100\n")

        # On lit strictement 2 octets binaires
        raw_bytes = self.connection.read(2)
        if len(raw_bytes) != 2:
            raise TimeoutError("Délai d'attente dépassé pour M100.")

        # Reconversion en entier 16 bits
        return struct.unpack('<H', raw_bytes)[0]

    def get_authorization_status(self) -> bool:
        """Demande si la machine est actuellement dans la zone autorisée (M102)."""
        self.connection.write(b"M102\n")

        # On lit strictement 1 octet
        raw_bytes = self.connection.read(1)
        if len(raw_bytes) != 1:
            raise TimeoutError("Délai d'attente dépassé pour M102.")

        # Convertit l'octet reçu en booléen (True si != 0, False sinon)
        return bool(raw_bytes[0])

    def get_aru_status(self) -> dict:
        """Demande l'état des capteurs de fin de course (M101)."""
        self.connection.write(b"M101\n")

        raw_bytes = self.connection.read(1)
        if len(raw_bytes) != 1:
            raise TimeoutError("Délai d'attente dépassé pour M101.")

        status_byte = raw_bytes[0]

        # Décodage des 4 bits indépendants
        return {
            'X_MIN': bool(status_byte & 0x01),
            'X_MAX': bool(status_byte & 0x02),
            'Y_MIN': bool(status_byte & 0x04),
            'Y_MAX': bool(status_byte & 0x08)
        }

    def set_motor_speed(self, axe: str, vitesse: int):
        """Envoie une consigne de vitesse au moteur (ex: axe='X', vitesse=-200)."""
        # Formate la chaîne (ex: "X-200\n") et l'envoie
        commande = f"{axe}{vitesse}\n"
        self.connection.write(commande.encode('ascii'))


if __name__ == "__main__":
    bridge = EmbroiderySerialBridge()
    if bridge.connect():
        try:
            # 1. Déplacement du moteur X à vitesse 100 pendant 3 secondes
            print("[Test] Déplacement X à 100...")
            bridge.set_motor_speed('X', 1000)
            time.sleep(3.0)

            # Arrêt du moteur X avant de passer à Y
            bridge.set_motor_speed('X', 0)
            print("[Test] Moteur X arrêté.")

            # 2. Déplacement du moteur Y à vitesse -100 pendant 3 secondes
            print("[Test] Déplacement Y à -100...")
            bridge.set_motor_speed('Y', -1000)
            time.sleep(3.0)

            # Arrêt du moteur Y
            bridge.set_motor_speed('Y', 0)
            print("[Test] Moteur Y arrêté.")

            # 3. Demande de la donnée v_autorise
            print("\n[Test] Demande de V_autorise (M100)...")
            valeur = bridge.get_v_autorise()
            print(f"[Succès] V_autorise reçue : {valeur}")

            # 4. Demande de l'état des capteurs
            print("\n[Test] Demande de l'état des capteurs de fin de course (M101)...")

            etats = bridge.get_aru_status()
            print(f"[Succès]  -> Axe X | MIN : {etats['X_MIN']} | MAX : {etats['X_MAX']}")
            print(f"[Succès]  -> Axe Y | MIN : {etats['Y_MIN']} | MAX : {etats['Y_MAX']}")

            # 5. Demande de l'état de la zone d'autorisation
            print("\n[Test] Demande de l'état d'autorisation (M102)...")
            t_start = time.perf_counter()

            autorise = bridge.get_authorization_status()

            t_end = time.perf_counter()
            print(f"[Succès] En zone autorisée : {autorise}")
            print(f"[Temps total PC] : {(t_end - t_start) * 1000:.3f} millisecondes")

        except Exception as e:
            print(f"[Erreur] {e}")

        finally:
            # SÉCURITÉ : S'assure que les moteurs s'arrêtent même si le script plante
            if bridge.connection and bridge.connection.is_open:
                try:
                    bridge.set_motor_speed('X', 0)
                    bridge.set_motor_speed('Y', 0)
                except:
                    pass
            bridge.close()