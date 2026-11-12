"""Petits composants réutilisables : voyant, tuile d'indicateur, titre de section."""
from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from . import theme


def panel(widget: QFrame) -> QFrame:
    widget.setProperty("panel", True)
    return widget


def section_title(text: str) -> QLabel:
    label = QLabel(text.upper())
    label.setProperty("role", "section")
    return label


def repolish(widget: QWidget) -> None:
    widget.style().unpolish(widget)
    widget.style().polish(widget)


class Led(QWidget):
    """Voyant rond. ``unknown`` dessine un anneau vide (donnée absente)."""

    def __init__(self, diameter: int = 14, parent=None) -> None:
        super().__init__(parent)
        self._d = diameter
        self._color = QColor(theme.INACTIVE)
        self._unknown = True
        self.setFixedSize(QSize(diameter + 6, diameter + 6))

    def set_level(self, level: str, unknown: bool = False) -> None:
        self._color = theme.color(level)
        self._unknown = unknown
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(3, 3, self._d, self._d)
        if self._unknown:
            p.setPen(QPen(self._color, 1.6, Qt.PenStyle.DashLine))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(r)
            return
        glow = QRadialGradient(r.center(), self._d)
        c = QColor(self._color)
        c.setAlpha(90)
        glow.setColorAt(0, c)
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(r.adjusted(-3, -3, 3, 3))
        p.setBrush(self._color)
        p.setPen(QPen(self._color.lighter(130), 1))
        p.drawEllipse(r)


class IndicatorTile(QFrame):
    """Voyant + nom du capteur + valeur + détail."""

    def __init__(self, title: str, source: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("tile")
        self.setStyleSheet(
            f"QFrame#tile {{ background: {theme.SURFACE_2}; border: 1px solid {theme.BORDER}; border-radius: 6px; }}"
            "QFrame#tile QLabel { background: transparent; }"
        )
        self.led = Led(13)
        self.title = QLabel(title)
        self.title.setStyleSheet(f"color: {theme.TEXT_DIM}; font-size: 8.5pt;")
        self.value = QLabel("—")
        self.value.setStyleSheet("font-weight: 600;")
        self.value.setWordWrap(True)
        self.detail = QLabel("")
        self.detail.setStyleSheet(f"color: {theme.TEXT_DIM}; font-size: 8pt;")
        self.detail.setWordWrap(True)
        self.title.setWordWrap(True)
        self.detail.setVisible(False)
        if source:
            self.setToolTip(source)

        text = QVBoxLayout()
        text.setSpacing(1)
        text.setContentsMargins(0, 0, 0, 0)
        text.addWidget(self.title)
        text.addWidget(self.value)
        text.addWidget(self.detail)
        row = QHBoxLayout(self)
        row.setContentsMargins(8, 6, 8, 6)
        row.setSpacing(8)
        row.addWidget(self.led, 0, Qt.AlignmentFlag.AlignTop)
        row.addLayout(text, 1)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def set_state(self, level: str, value: str, detail: str = "", unknown: bool = False) -> None:
        self.led.set_level(level, unknown)
        self.value.setText(value)
        color = theme.LEVEL_COLOR.get(level, theme.TEXT) if level in ("error", "warning") else theme.TEXT
        if unknown:
            color = theme.TEXT_DIM
        self.value.setStyleSheet(f"font-weight: 600; color: {color};")
        self.detail.setText(detail)
        self.detail.setVisible(bool(detail))
