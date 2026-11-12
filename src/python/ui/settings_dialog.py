"""Fenêtre Paramètres : sécurité, axes, limites, affichage, simulation."""
from __future__ import annotations

import copy

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QMessageBox,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from machine.config import AppConfig


def _spin(lo: float, hi: float, value: float, suffix: str, decimals: int = 2) -> QDoubleSpinBox:
    box = QDoubleSpinBox()
    box.setRange(lo, hi)
    box.setDecimals(decimals)
    box.setSuffix(suffix)
    box.setValue(value)
    return box


def _note(text: str) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    label.setProperty("role", "dim")
    return label


class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Paramètres")
        self.setMinimumWidth(520)
        self._original = config
        self.result_config: AppConfig | None = None
        tabs = QTabWidget()

        # Sécurité
        page = QWidget()
        form = QFormLayout(page)
        self.watchdog = QCheckBox("Activer le chien de garde à la connexion")
        self.watchdog.setChecked(config.safety.watchdog_enabled)
        self.watchdog_ms = QSpinBox()
        self.watchdog_ms.setRange(100, 5000)
        self.watchdog_ms.setSuffix(" ms")
        self.watchdog_ms.setValue(config.safety.watchdog_ms)
        self.watchdog.toggled.connect(self.watchdog_ms.setEnabled)
        self.watchdog_ms.setEnabled(config.safety.watchdog_enabled)
        self.margin = _spin(0, 50, config.limits.soft_margin_mm, " mm")
        self.pre_home = _spin(0.1, 100, config.limits.pre_home_speed_max_mm_s, " mm/s", 1)
        form.addRow(self.watchdog)
        form.addRow("Délai", self.watchdog_ms)
        form.addRow(_note("Sans ligne reçue pendant ce délai alors qu'un axe bouge, la carte arrête les axes. "
                          "Désactivé, un plantage du PC laisse les axes tourner jusqu'aux fins de course."))
        form.addRow("Marge des limites logicielles", self.margin)
        form.addRow("Vitesse max avant prise d'origine", self.pre_home)
        tabs.addTab(page, "Sécurité")

        # Axes
        page = QWidget()
        form = QFormLayout(page)
        self.spm_x = _spin(1, 10_000, config.x.steps_per_mm, " µpas/mm", 3)
        self.spm_y = _spin(1, 10_000, config.y.steps_per_mm, " µpas/mm", 3)
        self.travel_x_known = QCheckBox("connue")
        self.travel_y_known = QCheckBox("connue")
        self.travel_x = _spin(1, 5000, config.x.travel_mm or 100.0, " mm", 3)
        self.travel_y = _spin(1, 5000, config.y.travel_mm or 100.0, " mm", 3)
        for known, box, value in ((self.travel_x_known, self.travel_x, config.x.travel_mm),
                                  (self.travel_y_known, self.travel_y, config.y.travel_mm)):
            known.setChecked(value is not None)
            box.setEnabled(value is not None)
            known.toggled.connect(box.setEnabled)
        form.addRow("Pas X", self.spm_x)
        form.addRow("Pas Y", self.spm_y)
        form.addRow(_note("GT2 20 dents (40 mm/tour), 200 pas/tour, micropas 1/16 : 80 µpas/mm."))
        form.addRow("Course X", self.travel_x)
        form.addRow("", self.travel_x_known)
        form.addRow("Course Y", self.travel_y)
        form.addRow("", self.travel_y_known)
        form.addRow(_note("Distance entre les fins de course min et max. Mesure automatique : "
                          "Machine › Mesurer les courses. La saisie manuelle sert de secours."))
        tabs.addTab(page, "Axes")

        # Limites et réglages manuels
        page = QWidget()
        form = QFormLayout(page)
        self.vmax = _spin(1, 312, config.limits.speed_max_mm_s, " mm/s", 1)
        self.amax = _spin(1, 200_000, config.limits.accel_max_mm_s2, " mm/s²", 0)
        self.jog_speed = _spin(0.1, 312, config.manual.speed_mm_s, " mm/s", 1)
        self.jog_accel = _spin(1, 200_000, config.manual.accel_mm_s2, " mm/s²", 0)
        self.home_speed = _spin(0.1, 100, config.manual.home_speed_mm_s, " mm/s", 1)
        self.calib_speed = _spin(0.1, 100, config.manual.calibration_speed_mm_s, " mm/s", 1)
        form.addRow("Vitesse maximale", self.vmax)
        form.addRow("Accélération maximale", self.amax)
        form.addRow(_note("Plafonds tirés de calcul_stepper_moteur.xlsx (vitesse du coude 252 mm/s, 100 m/s²)."))
        form.addRow("Vitesse manuelle par défaut", self.jog_speed)
        form.addRow("Accélération manuelle par défaut", self.jog_accel)
        form.addRow("Vitesse de prise d'origine", self.home_speed)
        form.addRow("Vitesse de mesure des courses", self.calib_speed)
        self.line_vmax = _spin(1, 312, config.embroidery.line_speed_max_mm_s, " mm/s", 1)
        form.addRow("Vitesse max de la ligne de test", self.line_vmax)
        form.addRow(_note("La ligne de test utilise une consigne v1 sans rampe : le cadre démarre et s'arrête net "
                          "à chaque fenêtre aiguille. Augmenter seulement après essai."))
        tabs.addTab(page, "Limites")

        # Affichage
        page = QWidget()
        form = QFormLayout(page)
        self.show_grid = QCheckBox("Afficher la grille")
        self.show_grid.setChecked(config.view.show_grid)
        self.grid_step = _spin(1, 50, config.view.grid_step_mm, " mm", 0)
        form.addRow(self.show_grid)
        form.addRow("Pas de la grille", self.grid_step)
        form.addRow(_note("Zones interdites : section « view.forbidden_zones » du fichier de configuration."))
        tabs.addTab(page, "Affichage")

        # Simulation
        page = QWidget()
        form = QFormLayout(page)
        sim = config.simulation
        self.sim_tx = _spin(10, 5000, sim.travel_mm[0], " mm", 1)
        self.sim_ty = _spin(10, 5000, sim.travel_mm[1], " mm", 1)
        self.sim_sx = _spin(0, 5000, sim.start_mm[0], " mm", 1)
        self.sim_sy = _spin(0, 5000, sim.start_mm[1], " mm", 1)
        form.addRow(_note("Valeurs FICTIVES de la machine simulée, sans rapport avec la machine réelle. "
                          "Prises en compte à la prochaine connexion en simulation."))
        form.addRow("Course X simulée", self.sim_tx)
        form.addRow("Course Y simulée", self.sim_ty)
        form.addRow("Position de départ X", self.sim_sx)
        form.addRow("Position de départ Y", self.sim_sy)
        tabs.addTab(page, "Simulation")

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        lay = QVBoxLayout(self)
        lay.addWidget(tabs)
        lay.addWidget(buttons)

    def _build(self) -> AppConfig:
        cfg = copy.deepcopy(self._original)
        cfg.safety.watchdog_enabled = self.watchdog.isChecked()
        cfg.safety.watchdog_ms = self.watchdog_ms.value()
        cfg.limits.soft_margin_mm = self.margin.value()
        cfg.limits.pre_home_speed_max_mm_s = self.pre_home.value()
        cfg.x.steps_per_mm = self.spm_x.value()
        cfg.y.steps_per_mm = self.spm_y.value()
        cfg.x.travel_mm = self.travel_x.value() if self.travel_x_known.isChecked() else None
        cfg.y.travel_mm = self.travel_y.value() if self.travel_y_known.isChecked() else None
        cfg.limits.speed_max_mm_s = self.vmax.value()
        cfg.limits.accel_max_mm_s2 = self.amax.value()
        cfg.manual.speed_mm_s = min(self.jog_speed.value(), self.vmax.value())
        cfg.manual.accel_mm_s2 = min(self.jog_accel.value(), self.amax.value())
        cfg.manual.home_speed_mm_s = self.home_speed.value()
        cfg.manual.calibration_speed_mm_s = self.calib_speed.value()
        cfg.embroidery.line_speed_max_mm_s = self.line_vmax.value()
        cfg.view.show_grid = self.show_grid.isChecked()
        cfg.view.grid_step_mm = self.grid_step.value()
        cfg.simulation.travel_mm = [self.sim_tx.value(), self.sim_ty.value()]
        cfg.simulation.start_mm = [min(self.sim_sx.value(), self.sim_tx.value()),
                                   min(self.sim_sy.value(), self.sim_ty.value())]
        return cfg

    def _accept(self) -> None:
        cfg = self._build()
        errors = cfg.validate()
        if errors:
            QMessageBox.warning(self, "Paramètres invalides", "\n".join(errors))
            return
        if self._original.safety.watchdog_enabled and not cfg.safety.watchdog_enabled:
            answer = QMessageBox.warning(
                self, "Désactiver le chien de garde ?",
                "Sans chien de garde, si le PC ou l'application plante pendant un mouvement, "
                "les axes continuent jusqu'aux fins de course.\n\nDésactiver quand même ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        if (cfg.x.steps_per_mm, cfg.y.steps_per_mm) != (self._original.x.steps_per_mm,
                                                         self._original.y.steps_per_mm):
            QMessageBox.information(self, "Pas/mm modifiés",
                                    "Les courses enregistrées restent en mm : remesurez-les si besoin.")
        self.result_config = cfg
        self.accept()
