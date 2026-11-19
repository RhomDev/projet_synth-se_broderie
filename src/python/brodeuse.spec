# -*- mode: python ; coding: utf-8 -*-
# Build : pyinstaller brodeuse.spec   (depuis src/python, sous Windows pour obtenir un .exe)

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    # fichier de config par défaut, lu via resource_dir() / "config"
    datas=[("config/machine.default.json", "config")],
    hiddenimports=["serial.tools.list_ports"],
    # librairies listées dans requirements.txt mais non utilisées par l'appli : exe plus léger
    excludes=["matplotlib", "numpy", "svgpathtools", "tkinter", "unittest"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Brodeuse",
    console=False,   # mettre True pour voir les erreurs au démarrage
    # icon="icone.ico",
)
