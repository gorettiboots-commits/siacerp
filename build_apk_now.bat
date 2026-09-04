@echo off
cd /d "%~dp0mobile"
echo ========================================
echo   SIAC ERP — Build de APK (EAS Build)
echo ========================================
echo.
echo Ejecutando: eas build --platform android --profile production
echo Esto puede tardar 5-15 minutos...
echo.
call npx eas-cli build --platform android --profile production --non-interactive
echo.
echo ========================================
echo   Build finalizado
echo ========================================
echo Descargalo desde: https://expo.dev
pause
