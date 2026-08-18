@echo off
REM SIAC ERP - Launch Script
set "PYTHONPATH=%~dp0"
cd /d "%~dp0"
set "PYTHONW=%~dp0venv\Scripts\pythonw.exe"
if not exist "%PYTHONW%" set "PYTHONW=C:\Users\EskinBoots\AppData\Local\Programs\Python\Python312\pythonw.exe"
if exist "%PYTHONW%" (
    start "" "%PYTHONW%" main.py
    exit /b 0
)
start "" pythonw.exe main.py 2>nul
if errorlevel 1 start "" python main.py
