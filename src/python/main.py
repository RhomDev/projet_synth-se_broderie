"""Lanceur de l'interface de pilotage de la brodeuse.

Usage : python main.py [--simulation]
  --simulation   se connecte directement à la machine simulée
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def log_dir() -> Path:
    if sys.platform.startswith("win"):
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "Brodeuse"
    else:
        root = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "brodeuse"
    return root / "logs"


def setup_logging() -> Path:
    directory = log_dir()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "brodeuse.log"
    handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=5, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(name)s : %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(handler)
    console = logging.StreamHandler()
    console.setLevel(logging.WARNING)
    root.addHandler(console)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Pilotage de la brodeuse")
    parser.add_argument("--simulation", action="store_true", help="connexion directe à la machine simulée")
    args = parser.parse_args()

    log_path = setup_logging()
    from PySide6.QtWidgets import QApplication

    from machine.config import load_config
    from ui.main_window import MainWindow
    from ui.theme import apply_theme

    app = QApplication(sys.argv)
    app.setApplicationName("Brodeuse")
    app.setOrganizationName("Brodeuse")
    apply_theme(app)
    window = MainWindow(load_config())
    window.show()
    logging.getLogger("brodeuse").info("Démarrage ; journal : %s", log_path)
    if args.simulation:
        window.connect_simulation()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
