"""Thème sombre de type logiciel industriel : couleurs d'état et feuille de style Qt."""
from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import QApplication

BG = "#0f1216"
SURFACE = "#171b21"
SURFACE_2 = "#1f252d"
SURFACE_3 = "#28303a"
BORDER = "#2b323c"
TEXT = "#e7eaee"
TEXT_DIM = "#8d97a5"
ACCENT = "#3d9df3"

# Couleurs d'état imposées par le cahier des charges de l'IHM
OK = "#2fb36b"  # vert : capteur actif ou état normal
INACTIVE = "#59636f"  # gris : capteur inactif
ERROR = "#e5484d"  # rouge : défaut ou situation anormale
WARNING = "#f0a020"  # orange : avertissement

LEVEL_COLOR = {
    "ok": OK,
    "inactive": INACTIVE,
    "error": ERROR,
    "warning": WARNING,
    "active": ACCENT,
}

PLATE_FILL = "#161c23"
GRID_MINOR = "#1f2730"
GRID_MAJOR = "#2c3743"


def mono_font(point_size: float = 10, bold: bool = False) -> QFont:
    font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
    font.setPointSizeF(point_size)
    font.setBold(bold)
    return font


def color(level: str) -> QColor:
    return QColor(LEVEL_COLOR.get(level, INACTIVE))


STYLESHEET = f"""
QWidget {{ background: {BG}; color: {TEXT}; }}
QMainWindow::separator {{ background: {BORDER}; width: 1px; height: 1px; }}
QToolTip {{ background: {SURFACE_3}; color: {TEXT}; border: 1px solid {BORDER}; padding: 6px; }}

QFrame[panel="true"] {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; }}
QFrame[panel="true"] QLabel, QFrame[panel="true"] QCheckBox {{ background: transparent; }}
QLabel[role="section"] {{ color: {TEXT_DIM}; font-size: 8.5pt; font-weight: 600; letter-spacing: 1px; }}
QLabel[role="dim"] {{ color: {TEXT_DIM}; }}
QLabel[role="note"] {{ color: {WARNING}; font-size: 9pt; }}

QPushButton {{
    background: {SURFACE_2}; border: 1px solid {BORDER}; border-radius: 6px;
    padding: 7px 14px; color: {TEXT};
}}
QPushButton:hover {{ background: {SURFACE_3}; border-color: #3a4450; }}
QPushButton:pressed {{ background: {ACCENT}; color: #0b0e12; }}
QPushButton:checked {{ background: #1c3a57; border-color: {ACCENT}; color: {TEXT}; }}
QPushButton:disabled {{ color: #4d5661; background: #171b21; border-color: #22282f; }}
QPushButton[role="primary"] {{ background: #1d4f80; border-color: {ACCENT}; font-weight: 600; }}
QPushButton[role="primary"]:hover {{ background: #24609b; }}
QPushButton[role="primary"]:disabled {{ background: #171b21; border-color: #22282f; color: #4d5661; }}
QPushButton[role="pad"] {{ font-size: 15pt; font-weight: 600; min-width: 64px; min-height: 64px; padding: 0; }}
QPushButton[role="pad"]:pressed {{ background: {ACCENT}; }}
QPushButton[role="stop-pad"] {{
    background: #3a1517; border: 1px solid #7a2a2e; color: #ffb4b6;
    font-weight: 700; min-width: 64px; min-height: 64px; padding: 0;
}}
QPushButton[role="stop-pad"]:hover {{ background: #4a1a1d; }}
QPushButton[role="estop"] {{
    background: #c62f35; border: 2px solid #ff6a6f; color: white;
    font-size: 14pt; font-weight: 800; border-radius: 8px; padding: 6px 22px;
}}
QPushButton[role="estop"]:hover {{ background: #d9363d; }}
QPushButton[role="estop"]:pressed {{ background: #8f1f24; }}
QPushButton[role="segment"] {{ border-radius: 0; padding: 6px 10px; min-width: 44px; }}

QDoubleSpinBox, QSpinBox, QComboBox, QLineEdit {{
    background: {SURFACE_2}; border: 1px solid {BORDER}; border-radius: 5px;
    padding: 5px 8px; selection-background-color: {ACCENT};
}}
QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus, QLineEdit:focus {{ border-color: {ACCENT}; }}
QDoubleSpinBox:disabled, QSpinBox:disabled {{ color: #4d5661; }}

QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{ width: 16px; height: 16px; border: 1px solid #4a5563; border-radius: 3px; background: {SURFACE_2}; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}

QMenuBar {{ background: {SURFACE}; border-bottom: 1px solid {BORDER}; }}
QMenuBar::item {{ padding: 6px 12px; background: transparent; }}
QMenuBar::item:selected {{ background: {SURFACE_3}; }}
QMenu {{ background: {SURFACE}; border: 1px solid {BORDER}; padding: 4px; }}
QMenu::item {{ padding: 6px 24px 6px 18px; }}
QMenu::item:selected {{ background: {SURFACE_3}; }}
QMenu::item:disabled {{ color: #4d5661; }}
QMenu::separator {{ height: 1px; background: {BORDER}; margin: 4px 8px; }}

QStatusBar {{ background: {SURFACE}; border-top: 1px solid {BORDER}; color: {TEXT_DIM}; }}
QDockWidget {{ color: {TEXT_DIM}; }}
QDockWidget::title {{ background: {SURFACE}; padding: 6px 10px; border-top: 1px solid {BORDER}; }}
QPlainTextEdit {{ background: #0b0e11; border: none; }}
QScrollArea {{ border: none; }}
QScrollBar:vertical {{ background: transparent; width: 10px; }}
QScrollBar::handle:vertical {{ background: {SURFACE_3}; border-radius: 5px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QTabWidget::pane {{ border: 1px solid {BORDER}; border-radius: 6px; top: -1px; }}
QTabBar::tab {{ background: {SURFACE}; padding: 8px 16px; border: 1px solid {BORDER}; border-bottom: none;
               border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; color: {TEXT_DIM}; }}
QTabBar::tab:selected {{ background: {SURFACE_2}; color: {TEXT}; }}
"""


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    palette = QPalette()
    for role, value in (
        (QPalette.ColorRole.Window, BG),
        (QPalette.ColorRole.WindowText, TEXT),
        (QPalette.ColorRole.Base, SURFACE_2),
        (QPalette.ColorRole.AlternateBase, SURFACE),
        (QPalette.ColorRole.Text, TEXT),
        (QPalette.ColorRole.Button, SURFACE_2),
        (QPalette.ColorRole.ButtonText, TEXT),
        (QPalette.ColorRole.Highlight, ACCENT),
        (QPalette.ColorRole.HighlightedText, "#0b0e12"),
        (QPalette.ColorRole.ToolTipBase, SURFACE_3),
        (QPalette.ColorRole.ToolTipText, TEXT),
        (QPalette.ColorRole.PlaceholderText, TEXT_DIM),
    ):
        palette.setColor(role, QColor(value))
    app.setPalette(palette)
    font = app.font()
    font.setPointSizeF(10)
    app.setFont(font)  # taille par défaut ; pas dans la feuille de style, qui écraserait setFont()
    app.setStyleSheet(STYLESHEET)
