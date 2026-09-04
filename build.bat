@echo off
REM ============================================================
REM  SIAC ERP — Script de empaquetado con PyInstaller
REM  Genera el ejecutable en la carpeta dist/
REM ============================================================
setlocal

set "ROOT=%~dp0"
set "VENV=%ROOT%.venv\Scripts"

if not exist "%VENV%\python.exe" (
    echo [ERROR] No se encontro .venv. Ejecuta: python -m venv .venv
    pause
    exit /b 1
)

echo.
echo ========================================
echo   SIAC ERP — Empaquetado con PyInstaller
echo ========================================
echo.

REM 1) Verificar/instalar PyInstaller
"%VENV%\python.exe" -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Instalando PyInstaller...
    "%VENV%\python.exe" -m pip install pyinstaller --quiet
)

REM 2) Ejecutar PyInstaller con el spec
"%VENV%\python.exe" -m PyInstaller ^
    "%ROOT%siacerp.spec" ^
    --noconfirm ^
    --clean

if errorlevel 1 (
    echo.
    echo [ERROR] La compilacion fallo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Empaquetado exitoso
echo   Ejecutable: dist\SIAC_ERP\SIAC_ERP.exe
echo ========================================
echo.

REM 3) Abrir carpeta del ejecutable
explorer "%ROOT%dist\SIAC_ERP"

pause
