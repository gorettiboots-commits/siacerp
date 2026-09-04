@echo off
REM ============================================================
REM  SIAC ERP — Build completo: PyInstaller + NSIS
REM  Genera el instalador final en installer_output/
REM  NSIS es 100%% gratis para uso comercial (a diferencia de Inno Setup)
REM ============================================================
setlocal EnableDelayedExpansion

set "ROOT=%~dp0"
set "PY=%ROOT%.python_embed\python.exe"

if not exist "%PY%" (
    echo [ERROR] No se encontro .python_embed\python.exe
    pause
    exit /b 1
)

echo.
echo ========================================
echo   SIAC ERP — Build de Instalador (NSIS)
echo ========================================
echo.

REM 1) Verificar/instalar PyInstaller
"%PY%" -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Instalando PyInstaller...
    "%PY%" -m pip install pyinstaller --quiet
)

REM 2) Ejecutar PyInstaller
echo [1/3] Compilando ejecutable con PyInstaller...
"%PY%" -m PyInstaller ^
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

REM 3) Verificar NSIS
set "MAKENSIS="
if exist "C:\Program Files (x86)\NSIS\makensis.exe" (
    set "MAKENSIS=C:\Program Files (x86)\NSIS\makensis.exe"
) else if exist "C:\Program Files\NSIS\makensis.exe" (
    set "MAKENSIS=C:\Program Files\NSIS\makensis.exe"
) else (
    where makensis >nul 2>nul
    if not errorlevel 1 (
        set "MAKENSIS=makensis"
    )
)

if "%MAKENSIS%"=="" (
    echo.
    echo [ERROR] NSIS no encontrado.
    echo Descargalo desde: https://nsis.sourceforge.io/Download
    echo O instala desde: choco install nsis
    pause
    exit /b 1
)

echo [2/3] NSIS encontrado: %MAKENSIS%

REM 4) Compilar instalador con NSIS
echo [2/3] Generando instalador con NSIS...
"%MAKENSIS%" "%ROOT%installer.nsi"

if errorlevel 1 (
    echo.
    echo [ERROR] La compilacion del instalador fallo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Build completado exitosamente
echo   Instalador: installer_output\SIAC_ERP_Instalador_1.2.0.exe
echo ========================================
echo.

REM 5) Abrir carpeta del instalador
explorer "%ROOT%installer_output"

pause
