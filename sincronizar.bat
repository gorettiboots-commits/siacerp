@echo off
REM ============================================================
REM  SIAC ERP — Sincronizar con upstream + origin (fork workflow)
REM  1. Descarga cambios del repo original (upstream)
REM  2. Fusiona upstream → productivo1 (tu rama de trabajo)
REM  3. Descarga cambios de tu fork (origin)
REM ============================================================
title SIAC ERP — Sincronizando...
cd /d "%~dp0"

echo.
echo  ============================================
echo   SIAC ERP — Sincronizar (fork workflow)
echo  ============================================
echo.
echo  Remotes configurados:
echo    origin   = dealerbotai/siacerp (tu fork)
echo    upstream = gorettiboots-commits/siacerp (original)
echo.

REM Verificar que estamos en un repositorio git
git rev-parse --is-inside-work-tree >nul 2>&1
if %errorlevel% neq 0 (
    echo  [X] No se detectó un repositorio Git aquí.
    pause
    exit /b 1
)

REM Guardar rama actual
for /f "tokens=*" %%i in ('git branch --show-current') do set "RAMA_ACTUAL=%%i"
echo  Rama actual: %RAMA_ACTUAL%
echo.

REM Verificar si hay cambios locales sin commit
git status --porcelain | findstr /r "." >nul 2>&1
if %errorlevel% equ 0 (
    echo  [!] Tienes cambios locales sin commit:
    echo.
    git status --short
    echo.
    echo  Opciones:
    echo    [1] Guardar cambios (stash) antes de sincronizar
    echo    [2] Hacer commit rapido de todo
    echo    [3] Cancelar
    echo.
    set /p OPCION="Selecciona (1/2/3): "

    if "%OPCION%"=="1" (
        echo.
        echo  [*] Guardando cambios en stash...
        git stash push -m "stash automatico antes de sincronizar"
        set "STASH_HECHO=1"
        echo  [OK] Cambios guardados.
    ) else if "%OPCION%"=="2" (
        echo.
        set /p DESCRIPCION="Descripcion del commit: "
        if "%DESCRIPCION%"=="" set "DESCRIPCION=commit automatico antes de sincronizar"
        git add -A
        git commit -m "%DESCRIPCION%"
        echo  [OK] Commit realizado.
    ) else (
        echo  [*] Sincronizacion cancelada.
        pause
        exit /b 0
    )
)

REM PASO 1: Fetch upstream (repo original)
echo.
echo  [1/3] Descargando cambios del repo original (upstream)...
git fetch upstream
if %errorlevel% neq 0 (
    echo  [!] No se pudo conectar con upstream.
    echo      Verifica tu conexion a internet.
    echo      Continuando solo con origin...
    goto :solo_origin
)

REM PASO 2: Fusionar upstream → rama actual
echo  [2/3] Fusionando cambios de upstream en %RAMA_ACTUAL%...
git merge upstream/%RAMA_ACTUAL% --no-edit 2>nul
if %errorlevel% neq 0 (
    REM Si la rama no existe en upstream, intentar con main
    git merge upstream/main --no-edit 2>nul
    if %errorlevel% neq 0 (
        echo  [!] No se pudieron fusionar cambios de upstream.
        echo      Puede que haya conflictos. Revise manualmente.
    ) else (
        echo  [OK] Upstream/main fusionado.
    )
) else (
    echo  [OK] Upstream sincronizado.
)

:solo_origin
REM PASO 3: Fetch + pull de origin (tu fork)
echo  [3/3] Descargando cambios de origin...
git fetch origin
git pull --rebase origin %RAMA_ACTUAL%
if %errorlevel% neq 0 (
    echo.
    echo  [!] Conflicto al hacer pull de origin.
    echo      Intentando resolver...
    git rebase --abort 2>nul
    git pull origin %RAMA_ACTUAL%
)

echo.
echo  ============================================
echo   [OK] Sincronizacion completada
echo  ============================================
echo.
echo  Ultimos commits:
git log --oneline -8
echo.

REM Si hicimos stash, preguntar si quiere restaurar
if "%STASH_HECHO%"=="1" (
    echo  ¿Restaurar los cambios que guardaste?
    set /p RESTAURAR="(s/n): "
    if /i "%RESTAURAR%"=="s" (
        git stash pop
        echo  [OK] Cambios restaurados.
    )
)

pause
