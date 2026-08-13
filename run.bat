@echo off
REM SIAC ERP - Launch Script
set "PYTHONPATH=%~dp0"
cd /d "%~dp0"
REM Preferir el entorno virtual del proyecto (.venv real; 'venv' por compatibilidad)
set "PYTHONW=%~dp0.venv\Scripts\pythonw.exe"
if not exist "%PYTHONW%" set "PYTHONW=%~dp0venv\Scripts\pythonw.exe"
if exist "%PYTHONW%" (
    start "" "%PYTHONW%" main.py
    exit /b 0
)
REM Último recurso: pythonw del PATH
start "" pythonw.exe main.py 2>nul
if errorlevel 1 start "" python main.py
