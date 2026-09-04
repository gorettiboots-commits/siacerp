@echo off
REM ============================================================
REM  SIAC ERP — Build de APK (app móvil)
REM  Genera el APK con EAS Build (Expo Application Services)
REM ============================================================
setlocal

set "ROOT=%~dp0"
set "MOBILE=%ROOT%mobile"

echo.
echo ========================================
echo   SIAC ERP — Build de APK
echo ========================================
echo.

REM 1) Verificar Node.js
where node >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Node.js no encontrado. Instala desde: https://nodejs.org
    pause
    exit /b 1
)

REM 2) Verificar/instalar eas-cli
echo [1/4] Verificando EAS CLI...
cd "%MOBILE%"
call npx eas --version >nul 2>nul
if errorlevel 1 (
    echo Instalando EAS CLI...
    call npm install -g eas-cli@latest
    if errorlevel 1 (
        echo [ERROR] No se pudo instalar EAS CLI.
        pause
        exit /b 1
    )
)
echo EAS CLI OK.

REM 3) Verificar login de Expo
echo [2/4] Verificando sesion de Expo...
call npx eas whoami >nul 2>nul
if errorlevel 1 (
    echo.
    echo No hay sesion activa de Expo.
    echo Ejecutando: eas login
    echo.
    call npx eas login
    if errorlevel 1 (
        echo [ERROR] No se pudo iniciar sesion en Expo.
        pause
        exit /b 1
    )
)
echo Sesion de Expo OK.

REM 4) Build del APK
echo [3/4] Generando APK (build en la nube)...
echo Esto puede tardar 5-15 minutos...
echo.
call npx eas build --platform android --profile production --non-interactive

if errorlevel 1 (
    echo.
    echo [ERROR] El build fallo. Revisa el error arriba.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   APK generado exitosamente
echo   Descargalo desde: https://expo.dev
echo ========================================
echo.

REM 5) Abrir Expo en el navegador
start https://expo.dev

pause
