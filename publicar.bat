@echo off
REM ============================================================
REM  SIAC ERP — Publicar cambios a productivo1 (push)
REM  Hace commit de los cambios y los sube al repositorio remoto
REM ============================================================
title SIAC ERP — Publicando...
cd /d "%~dp0"

echo.
echo  ============================================
echo   SIAC ERP — Publicar a productivo1
echo  ============================================
echo.

REM Verificar que estamos en un repositorio git
git rev-parse --is-inside-work-tree >nul 2>&1
if %errorlevel% neq 0 (
    echo  [X] No se detectó un repositorio Git aquí.
    pause
    exit /b 1
)

REM Verificar rama actual
for /f "tokens=*" %%i in ('git branch --show-current') do set "RAMA_ACTUAL=%%i"
echo  Rama actual: %RAMA_ACTUAL%
echo.

REM Verificar si hay cambios para publicar
git status --porcelain | findstr /r "." >nul 2>&1
if %errorlevel% neq 0 (
    echo  [*] Cambios detectados:
    echo.
    git status --short
    echo.
    set /p DESCRIPCION="Describe los cambios (ej: 'agrego indices de BD'): "
    if "%DESCRIPCION%"=="" set "DESCRIPCION=actualizacion automatica"

    echo.
    echo  [*] Haciendo commit...
    git add -A
    git commit -m "%DESCRIPCION%"
    echo  [OK] Commit realizado.
) else (
    echo  [*] No hay cambios locales para commitear.
)

REM Verificar si hay commits pendientes de push
git log origin/%RAMA_ACTUAL%..HEAD --oneline 2>nul | findstr /r "." >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo  [*] Commits pendientes de subir:
    git log origin/%RAMA_ACTUAL%..HEAD --oneline
    echo.
    set /p CONFIRMAR="¿Subir a origin/%RAMA_ACTUAL%? (s/n): "
    if /i not "%CONFIRMAR%"=="s" (
        echo  [*] Publicación cancelada.
        pause
        exit /b 0
    )

    echo.
    echo  [*] Subiendo cambios a origin...
    git push origin %RAMA_ACTUAL%
    if %errorlevel% neq 0 (
        echo.
        echo  [X] Error al subir. Verifica tu conexión y permisos.
        pause
        exit /b 1
    )
    echo  [OK] Cambios subidos exitosamente.
) else (
    echo  [*] No hay commits pendientes de subir.
    echo  Todo está sincronizado con origin.
)

echo.
echo  ============================================
echo   [OK] Publicación completada
echo  ============================================
echo.
pause
