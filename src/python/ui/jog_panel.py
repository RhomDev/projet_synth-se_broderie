"""Panneau de pilotage manuel."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from . import theme
from .widgets import panel, section_title

# (ligne, colonne) -> (sx, sy, texte, infobulle)
PAD = {
    (0, 0): (-1, 1, "◤", "X− et Y+ simultanés"),
    (0, 1): (0, 1, "▲\nY+", "Y+"),
    (0, 2): (1, 1, "◥", "X+ et Y+ simultanés"),
    (1, 0): (-1, 0, "◀ X−", "X− (vers Xmin)"),
    (1, 2): (1, 0, "X+ ▶", "X+"),
    (2, 0): (-1, -1, "◣", "X− et Y− simultanés"),
    (2, 1): (0, -1, "Y−\n▼", "Y− (vers Ymin)"),
    (2, 2): (1, -1, "◢", "X+ et Y− simultanés"),
}


class JogPanel(QFrame):
    jog_pressed = Signal(int, int)
    jog_released = Signal()
    step_requested = Signal(float, float)
    stop_requested = Signal()
    goto_requested = Signal(float, float)
    home_requested = Signal()
    calibrate_requested = Signal()
    speed_changed = Signal(float)
    accel_changed = Signal(float)

    def __init__(self, increments: list[float], parent=None) -> None:
        super().__init__(parent)
        panel(self)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 14)
        lay.setSpacing(10)
        lay.addWidget(section_title("Pilotage manuel"))

        # Mode : continu (maintenir) ou pas à pas
        self._continuous = QPushButton("Continu")
        self._continuous.setToolTip("Déplacement tant que le bouton est maintenu")
        self._stepwise = QPushButton("Pas à pas")
        self._stepwise.setToolTip("Un clic = un incrément")
        mode_group = QButtonGroup(self)
        mode_row = QHBoxLayout()
        mode_row.setSpacing(0)
        for b in (self._continuous, self._stepwise):
            b.setCheckable(True)
            b.setProperty("role", "segment")
            mode_group.addButton(b)
            mode_row.addWidget(b)
        self._continuous.setChecked(True)
        mode_group.buttonToggled.connect(self._mode_changed)
        lay.addLayout(mode_row)

        self._inc_group = QButtonGroup(self)
        inc_row = QHBoxLayout()
        inc_row.setSpacing(0)
        self._inc_buttons = []
        for value in increments:
            b = QPushButton(f"{value:g}")
            b.setCheckable(True)
            b.setProperty("role", "segment")
            b.setProperty("increment", float(value))
            b.setToolTip(f"Incrément de {value:g} mm")
            self._inc_group.addButton(b)
            self._inc_buttons.append(b)
            inc_row.addWidget(b)
        if self._inc_buttons:
            self._inc_buttons[min(1, len(self._inc_buttons) - 1)].setChecked(True)
        inc_label = QLabel("mm")
        inc_label.setProperty("role", "dim")
        inc_row.addSpacing(8)
        inc_row.addWidget(inc_label)
        lay.addLayout(inc_row)

        # Pavé directionnel
        grid = QGridLayout()
        grid.setSpacing(6)
        self._pad_buttons: list[QPushButton] = []
        for (row, col), (sx, sy, text, tip) in PAD.items():
            b = QPushButton(text)
            b.setProperty("role", "pad")
            b.setToolTip(tip)
            b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            b.setAutoRepeat(False)
            b.pressed.connect(lambda sx=sx, sy=sy: self._pad_pressed(sx, sy))
            b.released.connect(self._pad_released)
            b.clicked.connect(lambda _=False, sx=sx, sy=sy: self._pad_clicked(sx, sy))
            grid.addWidget(b, row, col)
            self._pad_buttons.append(b)
        stop = QPushButton("STOP")
        stop.setProperty("role", "stop-pad")
        stop.setToolTip("Arrêt immédiat des axes (Échap)")
        stop.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        stop.clicked.connect(self.stop_requested)
        grid.addWidget(stop, 1, 1)
        lay.addLayout(grid)

        # Vitesse et accélération
        params = QGridLayout()
        params.setHorizontalSpacing(10)
        params.setVerticalSpacing(6)
        self.speed = QDoubleSpinBox()
        self.speed.setDecimals(1)
        self.speed.setSuffix(" mm/s")
        self.speed.setRange(0.1, 250.0)
        self.speed.setKeyboardTracking(False)
        self.speed.valueChanged.connect(self.speed_changed)
        self.accel = QDoubleSpinBox()
        self.accel.setDecimals(0)
        self.accel.setSuffix(" mm/s²")
        self.accel.setRange(1.0, 100_000.0)
        self.accel.setSingleStep(100.0)
        self.accel.setKeyboardTracking(False)
        self.accel.valueChanged.connect(self.accel_changed)
        params.addWidget(QLabel("Vitesse"), 0, 0)
        params.addWidget(self.speed, 0, 1)
        params.addWidget(QLabel("Accélération"), 1, 0)
        params.addWidget(self.accel, 1, 1)
        lay.addLayout(params)
        self.cap_note = QLabel()
        self.cap_note.setProperty("role", "note")
        self.cap_note.setWordWrap(True)
        self.cap_note.hide()
        lay.addWidget(self.cap_note)

        # Aller à une position
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background: {theme.BORDER};")
        lay.addWidget(line)
        lay.addWidget(section_title("Aller à une position"))
        goto = QGridLayout()
        goto.setHorizontalSpacing(8)
        goto.setVerticalSpacing(6)
        self.goto_x = self._coord_box("X")
        self.goto_y = self._coord_box("Y")
        self.goto_button = QPushButton("Aller à cette position…")
        self.goto_button.setProperty("role", "primary")
        self.goto_button.clicked.connect(
            lambda: self.goto_requested.emit(self.goto_x.value(), self.goto_y.value()))
        goto.addWidget(self.goto_x, 0, 0)
        goto.addWidget(self.goto_y, 0, 1)
        goto.addWidget(self.goto_button, 1, 0, 1, 2)
        lay.addLayout(goto)

        actions = QHBoxLayout()
        self.home_button = QPushButton("Prise d'origine…")
        self.home_button.setToolTip("Recherche de Xmin et Ymin, puis position = 0")
        self.home_button.clicked.connect(self.home_requested)
        self.calib_button = QPushButton("Mesurer les courses…")
        self.calib_button.setToolTip("Après la prise d'origine : avance lente jusqu'à Xmax puis Ymax")
        self.calib_button.clicked.connect(self.calibrate_requested)
        actions.addWidget(self.home_button)
        actions.addWidget(self.calib_button)
        lay.addLayout(actions)
        self.progress = QLabel()
        self.progress.setWordWrap(True)
        self.progress.setStyleSheet(f"color: {theme.ACCENT};")
        self.progress.hide()
        lay.addWidget(self.progress)
        self.reason = QLabel()
        self.reason.setWordWrap(True)
        self.reason.setProperty("role", "dim")
        lay.addWidget(self.reason)

        self._held = False
        self._mode_changed()

    @staticmethod
    def _coord_box(axis: str) -> QDoubleSpinBox:
        box = QDoubleSpinBox()
        box.setPrefix(f"{axis}  ")
        box.setSuffix(" mm")
        box.setDecimals(2)
        box.setRange(-9_999.0, 9_999.0)
        box.setMinimumWidth(120)
        box.setFont(theme.mono_font(10))
        return box

    # --------------------------------------------------------------- API

    @property
    def continuous(self) -> bool:
        return self._continuous.isChecked()

    @property
    def increment(self) -> float:
        b = self._inc_group.checkedButton()
        return float(b.property("increment")) if b else 0.0

    def set_values(self, speed: float, accel: float, speed_max: float, accel_max: float) -> None:
        for box, value, top in ((self.speed, speed, speed_max), (self.accel, accel, accel_max)):
            box.blockSignals(True)
            box.setMaximum(top)
            box.setValue(value)
            box.blockSignals(False)

    def update_state(self, can_move: bool, reason: str, homed: bool, cap: float | None,
                     can_home: bool, calibrating: bool) -> None:
        for b in self._pad_buttons:
            b.setEnabled(can_move and not calibrating)
        self.goto_button.setEnabled(can_move and homed and not calibrating)
        self.home_button.setEnabled(can_home and not calibrating)
        self.calib_button.setEnabled(can_home and homed and not calibrating)
        if cap is not None and self.speed.value() > cap:
            self.cap_note.setText(f"Vitesse limitée à {cap:g} mm/s tant que la prise d'origine n'est pas faite.")
            self.cap_note.show()
        else:
            self.cap_note.hide()
        self.reason.setText("" if can_move else f"Déplacements bloqués : {reason}")
        self.reason.setVisible(not can_move)
        if not can_move and self._held:
            self._pad_released()

    def set_progress(self, text: str) -> None:
        self.progress.setText(text)
        self.progress.setVisible(bool(text))

    def release_all(self) -> None:
        """Appelé si la fenêtre perd le focus pendant un jog."""
        if self._held:
            self._pad_released()

    # ----------------------------------------------------------- interne

    def _mode_changed(self, *args) -> None:
        for b in self._inc_buttons:
            b.setEnabled(not self.continuous)

    def _pad_pressed(self, sx: int, sy: int) -> None:
        if self.continuous:
            self._held = True
            self.jog_pressed.emit(sx, sy)

    def _pad_released(self) -> None:
        if self._held:
            self._held = False
            self.jog_released.emit()

    def _pad_clicked(self, sx: int, sy: int) -> None:
        if not self.continuous:
            inc = self.increment
            self.step_requested.emit(sx * inc, sy * inc)
