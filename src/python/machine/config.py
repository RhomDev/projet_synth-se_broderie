"""Paramètres de la machine et de l'application (fichier JSON).

Ordre de lecture : valeurs du code ← ``config/machine.default.json`` ← fichier
utilisateur (écrit par la fenêtre Paramètres). Une clé absente garde la valeur
précédente ; une valeur invalide est signalée et ignorée.

Fichier utilisateur :
- Linux   : ``$XDG_CONFIG_HOME/brodeuse/machine.json`` (``~/.config/brodeuse``)
- Windows : ``%APPDATA%\\Brodeuse\\machine.json``
"""
from __future__ import annotations

import json
import logging
import os
import sys
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from pathlib import Path

from .units import AxisUnits

log = logging.getLogger("brodeuse.config")


@dataclass
class AxisConfig:
    steps_per_mm: float = 80.0  # GT2 20 dents (40 mm/tour), 200 pas, 1/16
    travel_mm: float | None = None  # course entre fins de course ; None = non mesurée

    @property
    def units(self) -> AxisUnits:
        return AxisUnits(self.steps_per_mm)


@dataclass
class LimitsConfig:
    speed_max_mm_s: float = 250.0  # sous la vitesse du coude (252 mm/s, tableur)
    accel_max_mm_s2: float = 100_000.0  # 100 m/s², tableur ; plafond, pas une consigne
    pre_home_speed_max_mm_s: float = 10.0  # avant prise d'origine
    soft_margin_mm: float = 1.0  # marge des limites logicielles devant les fins de course


@dataclass
class ManualConfig:
    speed_mm_s: float = 20.0  # valeur prudente, à valider sur la machine
    accel_mm_s2: float = 1_000.0  # valeur prudente, à valider sur la machine
    home_speed_mm_s: float = 10.0
    calibration_speed_mm_s: float = 10.0
    increments_mm: list[float] = field(default_factory=lambda: [0.1, 1.0, 10.0, 100.0])


@dataclass
class EmbroideryConfig:
    line_speed_max_mm_s: float = 30.0  # consigne v1 sans rampe : démarrage net à chaque fenêtre
    line_length_mm: float = 50.0
    line_stitch_mm: float = 2.0


@dataclass
class SafetyConfig:
    watchdog_enabled: bool = True
    watchdog_ms: int = 500


@dataclass
class LinkConfig:
    poll_hz: float = 20.0
    reply_timeout_s: float = 0.2
    lost_after_timeouts: int = 3
    stale_after_s: float = 0.5  # état considéré inconnu au-delà


@dataclass
class ZoneConfig:
    name: str = "zone"
    x_mm: float = 0.0
    y_mm: float = 0.0
    width_mm: float = 0.0
    height_mm: float = 0.0

    def contains(self, x: float, y: float) -> bool:
        return self.x_mm <= x <= self.x_mm + self.width_mm and self.y_mm <= y <= self.y_mm + self.height_mm


@dataclass
class ViewConfig:
    show_grid: bool = True
    grid_step_mm: float = 10.0
    forbidden_zones: list[ZoneConfig] = field(default_factory=list)


@dataclass
class SimulationConfig:
    """Valeurs fictives du simulateur ; ce ne sont pas les dimensions de la machine."""

    travel_mm: list[float] = field(default_factory=lambda: [300.0, 200.0])
    start_mm: list[float] = field(default_factory=lambda: [120.0, 80.0])


@dataclass
class AppConfig:
    x: AxisConfig = field(default_factory=AxisConfig)
    y: AxisConfig = field(default_factory=AxisConfig)
    limits: LimitsConfig = field(default_factory=LimitsConfig)
    manual: ManualConfig = field(default_factory=ManualConfig)
    embroidery: EmbroideryConfig = field(default_factory=EmbroideryConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    link: LinkConfig = field(default_factory=LinkConfig)
    view: ViewConfig = field(default_factory=ViewConfig)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)

    def axis(self, name: str) -> AxisConfig:
        return self.x if name.upper() == "X" else self.y

    @property
    def common_units(self) -> AxisUnits:
        """Unités pour les réglages communs aux deux axes (A, V) : l'axe le plus fin,
        pour qu'aucun axe ne dépasse la limite exprimée en mm."""
        return AxisUnits(min(self.x.steps_per_mm, self.y.steps_per_mm))

    # ------------------------------------------------------------ JSON

    def to_dict(self) -> dict:
        d = asdict(self)
        return {"axes": {"x": d.pop("x"), "y": d.pop("y")}, **d}

    def validate(self) -> list[str]:
        errors = []
        for name in ("x", "y"):
            ax = self.axis(name)
            if ax.steps_per_mm <= 0:
                errors.append(f"axe {name} : pas/mm doit être > 0")
            if ax.travel_mm is not None and ax.travel_mm <= 2 * self.limits.soft_margin_mm:
                errors.append(f"axe {name} : course trop petite")
        lim = self.limits
        for label, value in (
            ("vitesse max", lim.speed_max_mm_s),
            ("accélération max", lim.accel_max_mm_s2),
            ("vitesse avant origine", lim.pre_home_speed_max_mm_s),
            ("vitesse manuelle", self.manual.speed_mm_s),
            ("accélération manuelle", self.manual.accel_mm_s2),
            ("vitesse de prise d'origine", self.manual.home_speed_mm_s),
            ("vitesse de mesure des courses", self.manual.calibration_speed_mm_s),
            ("vitesse max de la ligne de test", self.embroidery.line_speed_max_mm_s),
            ("longueur de la ligne de test", self.embroidery.line_length_mm),
            ("longueur de point", self.embroidery.line_stitch_mm),
        ):
            if value <= 0:
                errors.append(f"{label} doit être > 0")
        if lim.soft_margin_mm < 0:
            errors.append("la marge logicielle doit être ≥ 0")
        if self.safety.watchdog_ms and not 100 <= self.safety.watchdog_ms <= 5000:
            errors.append("chien de garde : 100 à 5000 ms")
        if self.link.poll_hz <= 0 or self.link.reply_timeout_s <= 0:
            errors.append("liaison : fréquence et délai doivent être > 0")
        if self.safety.watchdog_enabled and self.safety.watchdog_ms < 3 * 1000 / self.link.poll_hz:
            errors.append("chien de garde trop court pour la fréquence d'interrogation")
        return errors


def _apply(target, data: dict, path: str = "") -> None:
    """Recopie dans la dataclass ``target`` les clés connues de ``data``."""
    if not isinstance(data, dict):
        log.warning("%s : section ignorée (objet attendu)", path or "racine")
        return
    known = {f.name: f for f in fields(target)}
    for key, value in data.items():
        if key.startswith("_"):
            continue  # commentaires
        if key not in known:
            log.warning("%s%s : clé inconnue ignorée", path, key)
            continue
        current = getattr(target, key)
        if is_dataclass(current):
            _apply(current, value, f"{path}{key}.")
        elif key == "forbidden_zones":
            zones = []
            for z in value or []:
                zone = ZoneConfig()
                _apply(zone, z, f"{path}{key}[].")
                zones.append(zone)
            setattr(target, key, zones)
        else:
            setattr(target, key, value)


def config_from_dict(data: dict, base: AppConfig | None = None) -> AppConfig:
    cfg = base or AppConfig()
    data = dict(data)
    axes = data.pop("axes", {})
    if isinstance(axes, dict):
        for name in ("x", "y"):
            if name in axes:
                _apply(cfg.axis(name), axes[name], f"axes.{name}.")
    _apply(cfg, data)
    return cfg


# ---------------------------------------------------------------- fichiers


def resource_dir() -> Path:
    """Dossier des ressources (aussi dans l'exécutable PyInstaller)."""
    base = getattr(sys, "_MEIPASS", None)
    return Path(base) if base else Path(__file__).resolve().parent.parent


def default_config_path() -> Path:
    return resource_dir() / "config" / "machine.default.json"


def user_config_path() -> Path:
    if sys.platform.startswith("win"):
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "Brodeuse"
    else:
        root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "brodeuse"
    return root / "machine.json"


def load_config(user_path: Path | None = None) -> AppConfig:
    cfg = AppConfig()
    for path in (default_config_path(), user_path or user_config_path()):
        if not path.exists():
            continue
        try:
            cfg = config_from_dict(json.loads(path.read_text(encoding="utf-8")), cfg)
            log.info("Configuration lue : %s", path)
        except (OSError, ValueError, TypeError) as exc:
            log.error("Configuration illisible %s : %s", path, exc)
    errors = cfg.validate()
    if errors:
        log.error("Configuration invalide (%s) : valeurs par défaut utilisées", "; ".join(errors))
        cfg = AppConfig()
    return cfg


def save_config(cfg: AppConfig, user_path: Path | None = None) -> Path:
    errors = cfg.validate()
    if errors:
        raise ValueError("; ".join(errors))
    path = user_path or user_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(cfg.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)
    return path
