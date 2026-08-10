@echo off
REM Goretti ERP - Launch Script
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
    set "PYTHONPATH=%~dp0"
    start "" ".venv\Scripts\pythonw.exe" main.py
) else (
    start "" pythonw.exe main.py 2>nul
    if errorlevel 1 start "" python main.py
)
