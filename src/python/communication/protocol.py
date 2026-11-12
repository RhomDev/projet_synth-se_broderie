"""Protocole série de la brodeuse : trames v1 (firmware actuel) et v2 (proposé).

Ce module ne fait aucune entrée-sortie : il construit les octets à envoyer et
décode les réponses. Référence : docs/05_Logiciel_et_Firmware/Protocole_Serie.md

Les fonctions de construction des commandes v2 (``stop_all``, ``read_status``...)
vérifient les plages de valeurs avant tout envoi. Tant que le firmware v2 n'est pas
flashé, l'application les fait exécuter par le simulateur (« SIMULATION »).
"""
from __future__ import annotations

import re
import struct
from dataclasses import dataclass
from enum import IntEnum, IntFlag

# --------------------------------------------------------------------- constantes

TICK_HZ = 25_000  # fréquence du Timer 2 du firmware
SPEED_SCALE = 32_768  # vitesse firmware n -> n * TICK_HZ / SPEED_SCALE micropas/s
SPEED_MAX = 32_768
ACCEL_MAX = 16_000_000  # micropas/s²
WATCHDOG_MIN_MS = 100
WATCHDOG_MAX_MS = 5_000
LINE_MAX = 64
INT32_MIN, INT32_MAX = -(2**31), 2**31 - 1

MOTION_CODES = frozenset({120, 122, 123, 130})


class ProtocolError(Exception):
    """Réponse illisible ou incohérente avec la commande envoyée."""


# ------------------------------------------------------------------- types communs


@dataclass(frozen=True)
class Endstops:
    """État des 4 fins de course du plateau (True = appuyé)."""

    x_min: bool = False
    x_max: bool = False
    y_min: bool = False
    y_max: bool = False

    @classmethod
    def from_bits(cls, bits: int) -> "Endstops":
        return cls(bool(bits & 1), bool(bits & 2), bool(bits & 4), bool(bits & 8))

    def to_bits(self) -> int:
        return int(self.x_min) | int(self.x_max) << 1 | int(self.y_min) << 2 | int(self.y_max) << 3


class ErrorCode(IntEnum):
    UNKNOWN_COMMAND = 1
    BAD_PARAMETER = 2
    NOT_HOMED = 3
    HOMING_IN_PROGRESS = 4
    MANUAL_MODE_ONLY = 5
    ALARM_ACTIVE = 6
    MALFORMED_LINE = 7


ERROR_TEXT = {
    ErrorCode.UNKNOWN_COMMAND: "commande inconnue",
    ErrorCode.BAD_PARAMETER: "paramètre manquant ou hors plage",
    ErrorCode.NOT_HOMED: "origine non faite",
    ErrorCode.HOMING_IN_PROGRESS: "prise d'origine en cours",
    ErrorCode.MANUAL_MODE_ONLY: "commande réservée au mode manuel",
    ErrorCode.ALARM_ACTIVE: "alarme bloquante active (acquitter)",
    ErrorCode.MALFORMED_LINE: "ligne trop longue ou mal formée",
}


class Alarm(IntFlag):
    NONE = 0
    WATCHDOG = 1  # bloquant
    RX_ERROR = 2  # bloquant
    LIMIT_X = 4  # information : fin de course X touchée pendant un mouvement
    LIMIT_Y = 8  # information : fin de course Y touchée pendant un mouvement


BLOCKING_ALARMS = Alarm.WATCHDOG | Alarm.RX_ERROR

ALARM_TEXT = {
    Alarm.WATCHDOG: "chien de garde déclenché",
    Alarm.RX_ERROR: "erreur de réception série",
    Alarm.LIMIT_X: "fin de course X touchée pendant un mouvement",
    Alarm.LIMIT_Y: "fin de course Y touchée pendant un mouvement",
}

# ------------------------------------------------------------------------- v1


@dataclass(frozen=True)
class V1Query:
    """Requête v1 à réponse binaire de longueur fixe."""

    payload: bytes
    reply_length: int


V1_WINDOW_DURATION = V1Query(b"M100\n", 2)
V1_ENDSTOPS = V1Query(b"M101\n", 1)
V1_WINDOW_OPEN = V1Query(b"M102\n", 1)


def encode_speed_v1(axis: str, value: int) -> bytes:
    """Consigne de vitesse v1 (sans réponse) : ``X-200\\n``."""
    if axis not in ("X", "Y"):
        raise ValueError(f"axe inconnu : {axis!r}")
    _check_range("vitesse", value, -SPEED_MAX, SPEED_MAX)
    return f"{axis}{int(value)}\n".encode("ascii")


def decode_window_duration_v1(raw: bytes) -> int:
    """Réponse de M100 : uint16 little-endian (µs)."""
    if len(raw) != 2:
        raise ProtocolError(f"M100 : 2 octets attendus, {len(raw)} reçus")
    return struct.unpack("<H", raw)[0]


def decode_endstops_v1(raw: bytes) -> Endstops:
    """Réponse de M101 : un octet, bits 0..3."""
    if len(raw) != 1 or raw[0] > 0x0F:
        raise ProtocolError(f"M101 : réponse invalide {raw!r}")
    return Endstops.from_bits(raw[0])


def decode_window_open_v1(raw: bytes) -> bool:
    """Réponse de M102 : un octet, 0 ou 1."""
    if len(raw) != 1 or raw[0] > 1:
        raise ProtocolError(f"M102 : réponse invalide {raw!r}")
    return bool(raw[0])


@dataclass(frozen=True)
class V1Status:
    """Ce que le firmware v1 permet de lire (M101, M102, M100). Pas de position."""

    endstops: Endstops
    window_open: bool
    window_v1: int | None  # M100 : 16 bits, vaut 70 au démarrage (pas une mesure)


@dataclass(frozen=True)
class LegacySpeeds:
    """Ligne v1 ``X<vx> Y<vy>`` : vitesse immédiate, sans rampe ni réponse.

    Conservée par le firmware v2. En mode broderie, les pas ne sortent que fenêtre
    aiguille ouverte : c'est ce qui permet de piquer une ligne à vitesse constante.
    """

    vx: int | None = None
    vy: int | None = None

    code = 0
    expects_reply = False
    is_motion = True

    def __post_init__(self) -> None:
        if self.vx is None and self.vy is None:
            raise ValueError("au moins un axe")
        for label, v in (("X", self.vx), ("Y", self.vy)):
            if v is not None:
                _check_range(f"vitesse {label}", v, -SPEED_MAX, SPEED_MAX)

    @property
    def name(self) -> str:
        return "X/Y (v1)"

    def encode(self) -> bytes:
        words = [f"{a}{v}" for a, v in (("X", self.vx), ("Y", self.vy)) if v is not None]
        return (" ".join(words) + "\n").encode("ascii")

    def __str__(self) -> str:
        return self.encode().decode("ascii").strip()


# ------------------------------------------------------------------------- v2


@dataclass(frozen=True)
class Command:
    """Commande v2 : ``M<code>`` suivi de paramètres ``<lettre><entier>``."""

    code: int
    params: tuple[tuple[str, int], ...] = ()

    expects_reply = True

    @property
    def name(self) -> str:
        return f"M{self.code}"

    @property
    def is_motion(self) -> bool:
        return self.code in MOTION_CODES

    def encode(self) -> bytes:
        text = " ".join([self.name, *(f"{k}{v}" for k, v in self.params)])
        if len(text) > LINE_MAX:
            raise ValueError(f"ligne trop longue ({len(text)} > {LINE_MAX})")
        return (text + "\n").encode("ascii")

    def __str__(self) -> str:
        return self.encode().decode("ascii").strip()


def stop_all() -> Command:
    """M110 : arrêt immédiat des deux axes."""
    return Command(110)


def read_status() -> Command:
    """M111 : lecture de l'état complet."""
    return Command(111)


def set_mode(manual: bool) -> Command:
    """M112 : mode broderie (False) ou manuel (True)."""
    return Command(112, (("S", int(bool(manual))),))


def set_watchdog(timeout_ms: int) -> Command:
    """M113 : chien de garde ; 0 le coupe."""
    if timeout_ms != 0:
        _check_range("délai du chien de garde (ms)", timeout_ms, WATCHDOG_MIN_MS, WATCHDOG_MAX_MS)
    return Command(113, (("T", int(timeout_ms)),))


def clear_alarms() -> Command:
    """M114 : acquittement des alarmes."""
    return Command(114)


def set_speeds(vx: int | None = None, vy: int | None = None) -> Command:
    """M120 : consignes de vitesse avec rampe (unité firmware, signées)."""
    params = _axis_params(vx, vy, -SPEED_MAX, SPEED_MAX, "vitesse")
    return Command(120, params)


def set_motion_limits(accel: int | None = None, vmax: int | None = None) -> Command:
    """M121 : accélération (µpas/s²) et vitesse maximale (unité firmware)."""
    params: list[tuple[str, int]] = []
    if accel is not None:
        _check_range("accélération", accel, 1, ACCEL_MAX)
        params.append(("A", int(accel)))
    if vmax is not None:
        _check_range("vitesse maximale", vmax, 1, SPEED_MAX)
        params.append(("V", int(vmax)))
    if not params:
        raise ValueError("M121 : au moins A ou V")
    return Command(121, tuple(params))


def move_relative(dx: int | None = None, dy: int | None = None) -> Command:
    """M122 : déplacement relatif en micropas."""
    return Command(122, _axis_params(dx, dy, INT32_MIN, INT32_MAX, "déplacement"))


def move_absolute(x: int | None = None, y: int | None = None) -> Command:
    """M123 : déplacement absolu en micropas (origine requise)."""
    return Command(123, _axis_params(x, y, INT32_MIN, INT32_MAX, "position"))


def home(x: bool = True, y: bool = True, speed: int | None = None) -> Command:
    """M130 : prise d'origine sur Xmin et/ou Ymin."""
    if not (x or y):
        raise ValueError("M130 : au moins un axe")
    params = [("X", int(x)), ("Y", int(y))]
    if speed is not None:
        _check_range("vitesse de prise d'origine", speed, 1, SPEED_MAX)
        params.append(("F", int(speed)))
    return Command(130, tuple(params))


# ------------------------------------------------------------------ réponses v2


@dataclass(frozen=True)
class Reply:
    ok: bool
    code: int
    values: dict[str, int]
    error: ErrorCode | None
    raw: str

    @property
    def error_text(self) -> str:
        if self.error is None:
            return ""
        return ERROR_TEXT.get(self.error, f"erreur {int(self.error)}")


_TOKEN_LETTER = re.compile(r"^([A-Z])(-?\d+)$")
_TOKEN_FIELD = re.compile(r"^([a-z]+)=(-?\d+)$")
_COMMAND = re.compile(r"^M(\d+)$")


def parse_reply(line: str) -> Reply:
    """Décode une ligne ``ok M<code> ...`` ou ``err M<code> <n>``."""
    raw = line.strip()
    tokens = raw.split()
    if len(tokens) < 2 or tokens[0] not in ("ok", "err"):
        raise ProtocolError(f"réponse inattendue : {raw!r}")
    m = _COMMAND.match(tokens[1])
    if not m:
        raise ProtocolError(f"code de commande illisible : {raw!r}")
    code = int(m.group(1))
    if tokens[0] == "err":
        if len(tokens) != 3 or not tokens[2].isdigit():
            raise ProtocolError(f"erreur mal formée : {raw!r}")
        n = int(tokens[2])
        try:
            err = ErrorCode(n)
        except ValueError:
            raise ProtocolError(f"code d'erreur inconnu : {raw!r}") from None
        return Reply(False, code, {}, err, raw)
    values: dict[str, int] = {}
    for tok in tokens[2:]:
        mm = _TOKEN_FIELD.match(tok) or _TOKEN_LETTER.match(tok)
        if not mm:
            raise ProtocolError(f"champ illisible {tok!r} dans {raw!r}")
        values[mm.group(1)] = int(mm.group(2))
    return Reply(True, code, values, None, raw)


@dataclass(frozen=True)
class MachineStatus:
    """Contenu de la ligne d'état ``M111``."""

    t_ms: int
    x: int
    y: int
    vx: int
    vy: int
    endstops: Endstops
    window_open: bool
    manual_mode: bool
    homed_x: bool
    homed_y: bool
    moving_x: bool
    moving_y: bool
    alarms: Alarm
    window_us: int

    FIELDS = ("t", "x", "y", "vx", "vy", "es", "win", "mode", "home", "mv", "al", "va")

    @classmethod
    def from_reply(cls, reply: Reply) -> "MachineStatus":
        if not reply.ok or reply.code != 111:
            raise ProtocolError(f"pas une ligne d'état : {reply.raw!r}")
        missing = [f for f in cls.FIELDS if f not in reply.values]
        if missing:
            raise ProtocolError(f"champs manquants {missing} dans {reply.raw!r}")
        v = reply.values
        return cls(
            t_ms=v["t"],
            x=v["x"],
            y=v["y"],
            vx=v["vx"],
            vy=v["vy"],
            endstops=Endstops.from_bits(v["es"]),
            window_open=bool(v["win"]),
            manual_mode=bool(v["mode"]),
            homed_x=bool(v["home"] & 1),
            homed_y=bool(v["home"] & 2),
            moving_x=bool(v["mv"] & 1),
            moving_y=bool(v["mv"] & 2),
            alarms=Alarm(v["al"] & 0x0F),
            window_us=v["va"],
        )

    @property
    def moving(self) -> bool:
        return self.moving_x or self.moving_y

    @property
    def homed(self) -> bool:
        return self.homed_x and self.homed_y

    @property
    def blocking_alarm(self) -> bool:
        return bool(self.alarms & BLOCKING_ALARMS)


def format_status(s: MachineStatus) -> str:
    """Ligne d'état telle que l'envoie le firmware v2 (utilisée par le simulateur)."""
    home = int(s.homed_x) | int(s.homed_y) << 1
    mv = int(s.moving_x) | int(s.moving_y) << 1
    return (
        f"ok M111 t={s.t_ms} x={s.x} y={s.y} vx={s.vx} vy={s.vy} es={s.endstops.to_bits()} "
        f"win={int(s.window_open)} mode={int(s.manual_mode)} home={home} mv={mv} "
        f"al={int(s.alarms)} va={s.window_us}"
    )


# ---------------------------------------------------------------------- outils


def _check_range(label: str, value: int, lo: int, hi: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{label} : entier attendu, reçu {value!r}")
    if not lo <= value <= hi:
        raise ValueError(f"{label} hors plage : {value} (attendu {lo} à {hi})")


def _axis_params(x: int | None, y: int | None, lo: int, hi: int, label: str) -> tuple[tuple[str, int], ...]:
    params: list[tuple[str, int]] = []
    if x is not None:
        _check_range(f"{label} X", x, lo, hi)
        params.append(("X", int(x)))
    if y is not None:
        _check_range(f"{label} Y", y, lo, hi)
        params.append(("Y", int(y)))
    if not params:
        raise ValueError(f"{label} : au moins un axe")
    return tuple(params)
