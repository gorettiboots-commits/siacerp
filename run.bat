@echo off
REM Goretti ERP - Launch Script
set "PYTHONPATH=%~dp0"
set "PATH=C:\Users\goret\AppData\Local\Programs\Python\Python311;C:\Users\goret\AppData\Local\Programs\Python\Python311\Scripts;%PATH%"
cd /d "%~dp0"
start "" pythonw.exe main.py 2>nul
if errorlevel 1 start "" python main.py
