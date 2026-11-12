"""Journal des échanges série et des messages de l'application."""
from __future__ import annotations

import html
import time

from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

from . import theme

COLORS = {
    "TX": theme.ACCENT,
    "RX": "#7fc8a0",
    "INFO": theme.TEXT_DIM,
    "info": theme.TEXT,
    "warning": theme.WARNING,
    "error": theme.ERROR,
}
LABELS = {"TX": "→ TX", "RX": "← RX", "INFO": "· liaison", "info": "· info", "warning": "! attention",
          "error": "✖ erreur"}


class LogPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setMaximumBlockCount(5000)
        self.text.setFont(theme.mono_font(9))
        self.show_polls = QCheckBox("Afficher l'interrogation d'état (M111, 20 Hz)")
        clear = QPushButton("Effacer")
        clear.clicked.connect(self.text.clear)
        bar = QHBoxLayout()
        bar.setContentsMargins(8, 4, 8, 0)
        bar.addWidget(self.show_polls)
        bar.addStretch(1)
        bar.addWidget(clear)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        lay.addLayout(bar)
        lay.addWidget(self.text)

    def add_traffic(self, direction: str, text: str, poll: bool) -> None:
        if poll and not self.show_polls.isChecked():
            return
        self._append(direction, text)

    def add_message(self, level: str, text: str) -> None:
        self._append(level, text)

    def _append(self, kind: str, text: str) -> None:
        stamp = time.strftime("%H:%M:%S") + f".{int(time.time() * 1000) % 1000:03d}"
        color = COLORS.get(kind, theme.TEXT)
        label = LABELS.get(kind, kind)
        self.text.appendHtml(
            f'<span style="color:{theme.TEXT_DIM}">{stamp}</span>&nbsp;&nbsp;'
            f'<span style="color:{color}">{html.escape(label):<11}</span>&nbsp;'
            f'<span style="color:{color}">{html.escape(text)}</span>'
        )
