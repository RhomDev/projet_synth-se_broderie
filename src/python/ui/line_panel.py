"""Panneau « Ligne de test » : piquer une ligne droite pour un premier essai."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from machine.config import AppConfig
from machine.line_test import LinePlan, plan_line
from machine.safety import can_move
from machine.state import MachineModel

from . import theme
from .widgets import panel, section_title


def _spin(lo: float, hi: float, value: float, suffix: str, decimals: int) -> QDoubleSpinBox:
    box = QDoubleSpinBox()
    box.setRange(lo, hi)
    box.setDecimals(decimals)
    box.setSuffix(suffix)
    box.setValue(value)
    box.setKeyboardTracking(False)
    return box


class LinePanel(QFrame):
    arm_requested = Signal(object)  # LinePlan
    stop_requested = Signal()
    preview_changed = Signal(object)  # LinePlan | None

    def __init__(self, config: AppConfig, parent=None) -> None:
        super().__init__(parent)
        panel(self)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 14)
        lay.setSpacing(10)
        lay.addWidget(section_title("Ligne de test (broderie)"))
        intro = QLabel(
            "Le cadre avance à vitesse constante, mais la carte n'émet les pas que pendant la fenêtre "
            "aiguille : chaque tour de machine fait un point. Armez la ligne, puis lancez la machine à coudre.")
        intro.setWordWrap(True)
        intro.setProperty("role", "dim")
        lay.addWidget(intro)

        e = config.embroidery
        self.length = _spin(1, 1000, e.line_length_mm, " mm", 1)
        self.angle = _spin(-360, 360, 0.0, " °", 1)
        self.stitch = _spin(0.1, 12, e.line_stitch_mm, " mm", 2)
        self.manual_window = QCheckBox("Saisir la fenêtre")
        self.window_ms = _spin(1, 500, 30.0, " ms", 1)
        self.window_ms.setEnabled(False)
        self.manual_window.toggled.connect(self.window_ms.setEnabled)
        self.measured = QLabel("—")
        self.measured.setProperty("role", "dim")

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(6)
        grid.addWidget(QLabel("Longueur"), 0, 0)
        grid.addWidget(self.length, 0, 1)
        grid.addWidget(QLabel("Direction"), 1, 0)
        grid.addWidget(self.angle, 1, 1)
        dirs = QHBoxLayout()
        dirs.setSpacing(0)
        for text, value in (("X+", 0.0), ("Y+", 90.0), ("X−", 180.0), ("Y−", 270.0)):
            b = QPushButton(text)
            b.setProperty("role", "segment")
            b.clicked.connect(lambda _=False, v=value: self.angle.setValue(v))
            dirs.addWidget(b)
        grid.addLayout(dirs, 2, 1)
        grid.addWidget(QLabel("Longueur de point"), 3, 0)
        grid.addWidget(self.stitch, 3, 1)
        grid.addWidget(QLabel("Fenêtre aiguille"), 4, 0)
        grid.addWidget(self.measured, 4, 1)
        grid.addWidget(self.manual_window, 5, 0)
        grid.addWidget(self.window_ms, 5, 1)
        lay.addLayout(grid)

        self.summary = QLabel()
        self.summary.setWordWrap(True)
        self.summary.setFont(theme.mono_font(9))
        lay.addWidget(self.summary)
        self.reason = QLabel()
        self.reason.setWordWrap(True)
        self.reason.setProperty("role", "note")
        lay.addWidget(self.reason)

        buttons = QHBoxLayout()
        self.arm = QPushButton("Armer la ligne…")
        self.arm.setProperty("role", "primary")
        self.arm.clicked.connect(self._arm)
        self.stop = QPushButton("Arrêter la ligne")
        self.stop.clicked.connect(self.stop_requested)
        self.stop.setEnabled(False)
        buttons.addWidget(self.arm)
        buttons.addWidget(self.stop)
        lay.addLayout(buttons)
        self.progress = QLabel()
        self.progress.setWordWrap(True)
        self.progress.setStyleSheet(f"color: {theme.ACCENT};")
        lay.addWidget(self.progress)
        lay.addStretch(1)

        self._plan: LinePlan | None = None
        self._running = False
        self._last_key = None
        for box in (self.length, self.angle, self.stitch, self.window_ms):
            box.valueChanged.connect(lambda *_: self._invalidate())
        self.manual_window.toggled.connect(lambda *_: self._invalidate())

    # --------------------------------------------------------------- API

    def refresh(self, model: MachineModel, config: AppConfig) -> None:
        st = model.status if model.protocol == 2 else None
        window_s = self._window_s(st)
        if st is not None and model.fresh and st.window_us:
            self.measured.setText(f"{st.window_us / 1000:.1f} ms (dernière mesure)")
        else:
            self.measured.setText("non mesurée : faites tourner la machine")
        if self._running:
            return
        if model.protocol == 1:
            plan, reason = None, "firmware v1 : flashez le firmware v2 (position et chien de garde nécessaires)"
        else:
            decision = can_move(model.state, st)
            if not decision:
                plan, reason = None, decision.reason
            else:
                plan, d = plan_line(config, st, self.length.value(), self.angle.value(),
                                    self.stitch.value(), window_s)
                reason = d.reason
        # La ligne part de la position actuelle ; l'aperçu n'est redessiné que s'il change
        key =(plan.x0, plan.y0, plan.x1, plan.y1, plan.vx_fw, plan.vy_fw) if plan else None
        self._plan = plan
        self.arm.setEnabled(plan is not None)
        self.reason.setText(reason)
        self.reason.setVisible(bool(reason))
        if plan:
            self.summary.setText(
                f"Cadre {plan.speed_mm_s:.1f} mm/s · ≈ {plan.stitches} points\n"
                f"Départ  X {plan.x0:8.2f}  Y {plan.y0:8.2f} mm\n"
                f"Arrivée X {plan.x1:8.2f}  Y {plan.y1:8.2f} mm")
        else:
            self.summary.setText("")
        if key != self._last_key:
            self._last_key = key
            self.preview_changed.emit(plan)

    def set_running(self, running: bool) -> None:
        self._running = running
        self.arm.setEnabled(not running and self._plan is not None)
        self.stop.setEnabled(running)
        for w in (self.length, self.angle, self.stitch, self.manual_window, self.window_ms):
            w.setEnabled(not running and (w is not self.window_ms or self.manual_window.isChecked()))

    def set_progress(self, text: str) -> None:
        self.progress.setText(text)

    # ----------------------------------------------------------- interne

    def _window_s(self, st) -> float:
        if self.manual_window.isChecked():
            return self.window_ms.value() / 1000
        return st.window_us / 1e6 if (st is not None and st.window_us) else 0.0

    def _invalidate(self) -> None:
        self._last_key = ("invalide",)

    def _arm(self) -> None:
        if self._plan is not None:
            self.arm_requested.emit(self._plan)
