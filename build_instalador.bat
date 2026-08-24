@echo off
REM ============================================================
REM  SIAC ERP — Build completo: PyInstaller + Inno Setup
REM  Genera el instalador final en installer_output/
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
echo   SIAC ERP — Build de Instalador
echo ========================================
echo.

REM 1) Verificar/instalar PyInstaller
"%VENV%\python.exe" -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Instalando PyInstaller...
    "%VENV%\python.exe" -m pip install pyinstaller --quiet
)

REM 2) Ejecutar PyInstaller
echo [1/3] Compilando ejecutable con PyInstaller...
"%VENV%\python.exe" -m PyInstaller ^
    "%ROOT%siacerp.spec" ^
    --noconfirm ^
    --clean

if errorlevel 1 (
    echo.
    echo [ERROR] La compilacion con PyInstaller fallo.
    pause
    exit /b 1
)

echo [1/3] Compilacion exitosa.

REM 3) Verificar Inno Setup
where iscc >nul 2>nul
if errorlevel 1 (
    echo.
    echo [ERROR] Inno Setup no encontrado en PATH.
    echo Descargalo desde: https://jrsoftware.org/isinfo.php
    echo O instala desde: winget install JRSoftware.InnoSetup
    pause
    exit /b 1
)

REM 4) Compilar instalador con Inno Setup
echo [2/3] Generando instalador con Inno Setup...
iscc "%ROOT%installer.iss"

if errorlevel 1 (
    echo.
    echo [ERROR] La compilacion del instalador fallo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Build completado exitosamente
echo   Instalador: installer_output\SIAC_ERP_Instalador_1.0.0.exe
echo ========================================
echo.

REM 5) Abrir carpeta del instalador
explorer "%ROOT%installer_output"

pause
