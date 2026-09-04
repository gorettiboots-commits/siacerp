@echo off
title SIAC ERP
cd /d "%~dp0"
set "PYTHONPATH=%~dp0"

REM Buscar Python
set "PY="
where python >nul 2>&1
if %errorlevel%==0 set "PY=python"

if "%PY%"=="" if exist ".python_embed\python.exe" set "PY=.python_embed\python.exe"

if "%PY%"=="" (
  echo Instalando Python...
  mkdir ".python_embed" 2>nul
  certutil -urlcache -split -f "https://www.python.org/ftp/python/3.12.7/python-3.12.7-embed-amd64.zip" "%TEMP%\py.zip" >nul 2>&1
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Path '%TEMP%\py.zip' -DestinationPath '%cd%\.python_embed' -Force" 2>nul
  echo import site>> ".python_embed\python312._pth"
  ".python_embed\python.exe" -m ensurepip --upgrade >nul 2>&1
  del "%TEMP%\py.zip" 2>nul
  set "PY=.python_embed\python.exe"
)

if "%PY%"=="" (
  echo No se pudo instalar Python.
  echo Descarga: https://www.python.org/downloads/
  pause
  exit /b 1
)

echo Python: %PY%
%PY% --version

REM Instalar dependencias
echo Instalando dependencias...
%PY% -m pip install -r requirements.txt --quiet 2>nul
%PY% -m pip install -r requirements-dev.txt --quiet 2>nul

REM Lanzar
echo Iniciando SIAC ERP...
start "" "%PY%" main.py
