@echo off
REM ============================================================
REM  SIAC ERP — Release: productivo1 → main (fork workflow)
REM  1. Fusiona productivo1 → main
REM  2. Sube main a origin (tu fork)
REM  3. Crea tag de release
REM  4. Opcionalmente crea PR al upstream (repo original)
REM ============================================================
title SIAC ERP — Release...
cd /d "%~dp0"

echo.
echo  ============================================
echo   SIAC ERP — Release (fork workflow)
echo  ============================================
echo.
echo  Flujo:
echo    productivo1 → main → origin (tu fork)
echo    Opcional: PR a upstream (repo original gorettiboots)
echo.

REM Verificar repositorio
git rev-parse --is-inside-work-tree >nul 2>&1
if %errorlevel% neq 0 (
    echo  [X] No se detecto un repositorio Git aqui.
    pause
    exit /b 1
)

REM Verificar que productivo1 tenga commits pendientes para main
git log main..productivo1 --oneline 2>nul | findstr /r "." >nul 2>&1
if %errorlevel% neq 0 (
    echo  [!] No hay commits nuevos en productivo1 para fusionar a main.
    echo      Main ya esta actualizado.
    echo.
    pause
    exit /b 0
)

echo  [*] Commits que se fusionaran a main:
echo.
git log main..productivo1 --oneline
echo.

REM Verificar que no haya cambios sin commit
git status --porcelain | findstr /r "." >nul 2>&1
if %errorlevel% equ 0 (
    echo  [!] Hay cambios sin commit en productivo1.
    echo      Haz commit primero con publicar.bat
    echo.
    pause
    exit /b 1
)

REM Confirmar
echo  ¿Fusionar estos commits a main?
set /p CONFIRMAR="(s/n): "
if /i not "%CONFIRMAR%"=="s" (
    echo  [*] Release cancelado.
    pause
    exit /b 0
)

REM Cambiar a main y actualizar
echo.
echo  [1/6] Cambiando a main...
git checkout main
if %errorlevel% neq 0 (
    echo  [X] Error al cambiar a main.
    pause
    exit /b 1
)

echo  [2/6] Actualizando main desde origin...
git pull origin main

REM Merge de productivo1
echo  [3/6] Fusionando productivo1 → main...
git merge productivo1 --no-edit
if %errorlevel% neq 0 (
    echo.
    echo  [X] Conflicto de merge.
    echo      Resuelve los conflictos manualmente y luego ejecuta:
    echo        git add .
    echo        git commit
    echo        git push origin main
    echo        git checkout productivo1
    echo.
    pause
    exit /b 1
)

REM Crear tag de release
echo.
echo  [4/6] Creando tag de release...
echo  (Ultimo tag:)
git describe --tags --abbrev=0 2>nul
echo.
set /p VERSION="Numero de version (ej: v1.2.0): "
if "%VERSION%"=="" (
    echo  [*] Tag cancelado. El merge ya se hizo.
    pause
    exit /b 0
)

git tag -a %VERSION% -m "Release %VERSION%"
echo  [OK] Tag %VERSION% creado.

REM Subir a origin (tu fork)
echo.
echo  [5/6] Subiendo main + tag a origin (tu fork)...
git push origin main
git push origin %VERSION%
if %errorlevel% neq 0 (
    echo.
    echo  [!] Error al subir a origin.
    echo      Sube manualmente:
    echo        git push origin main
    echo        git push origin %VERSION%
)

REM Preguntar si quiere crear PR al upstream
echo.
echo  [6/6] ¿Crear PR al upstream (repo original)?
echo        Esto abre GitHub para crear un Pull Request
echo        de main → gorettiboots-commits/siacerp:main
echo.
set /p CREAR_PR="(s/n): "
if /i "%CREAR_PR%"=="s" (
    echo.
    echo  [*] Abriendo GitHub para crear PR...
    start "" "https://github.com/gorettiboots-commits/siacerp/compare/main...dealerbotai:siacerp:main?expand=1"
    echo  [OK] GitHub abierto. Crea el Pull Request desde ahi.
)

echo.
echo  ============================================
echo   [OK] Release %VERSION% completado
echo  ============================================
echo.
echo   productivo1 → main     ✓
echo   Tag %VERSION%           ✓
echo   Subido a origin        ✓
echo.

REM Volver a productivo1
echo  Volviendo a productivo1...
git checkout productivo1
echo  Listo. Puedes seguir trabajando en productivo1.
echo.
pause
