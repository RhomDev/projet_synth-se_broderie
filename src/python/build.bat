@echo off
REM Construit dist\Brodeuse.exe (à lancer depuis src\python)
python -m pip install pyinstaller pyserial PySide6-Essentials
pyinstaller --noconfirm --clean brodeuse.spec
echo.
echo Termine : dist\Brodeuse.exe
pause
