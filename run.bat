@echo off
REM SIAC ERP - Launch Script
set "PYTHONPATH=%~dp0"
set "PYTHONW=%~dp0venv\Scripts\pythonw.exe"
if not exist "%PYTHONW%" set "PYTHONW=C:\Users\EskinBoots\AppData\Local\Programs\Python\Python312\pythonw.exe"
cd /d "%~dp0"
start "" "%PYTHONW%" main.py
if errorlevel 1 start "" python main.py
