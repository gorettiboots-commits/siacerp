; ============================================================
; SIAC ERP — NSIS Installer Script
; Solo copia archivos. La app maneja su propio onboarding.
; ============================================================

!include "MUI2.nsh"
!include "LogicLib.nsh"

; ── Configuracion ──────────────────────────────────────────
Name "SIAC ERP"
OutFile "installer_output\SIAC_ERP_Instalador_1.2.1.exe"
InstallDir "$PROGRAMFILES\SIAC ERP"
InstallDirRegKey HKLM "Software\SIAC ERP" "InstallDir"
RequestExecutionLevel admin

; ── Iconos ─────────────────────────────────────────────────
!define MUI_ICON "src\views\assets\siac_icono.ico"
!define MUI_UNICON "src\views\assets\siac_icono.ico"
!define MUI_ABORTWARNING
!define MUI_WELCOMEPAGE_TITLE "Bienvenido al Asistente de Instalacion de SIAC ERP"
!define MUI_WELCOMEPAGE_TEXT "Este asistente le guiara a traves de la instalacion del sistema integral de administracion y control.$\r$\n$\r$\nAl iniciar la app por primera vez, le pedira configurar los datos de su empresa y crear el usuario administrador.$\r$\n$\r$\nHaga clic en Siguiente para continuar."

; ── Paginas ────────────────────────────────────────────────
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

; Pagina final: ejecutar la app despues de instalar
!define MUI_FINISHPAGE_RUN "$INSTDIR\SIAC_ERP.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Iniciar SIAC ERP ahora"
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "Spanish"

; ============================================================
; SECCION: Instalacion
; ============================================================
Section "Instalar SIAC ERP" SecMain

    SetOutPath "$INSTDIR"
    File /r "dist\SIAC_ERP\*.*"

    ; Accesos directos
    CreateShortcut "$DESKTOP\SIAC ERP.lnk" "$INSTDIR\SIAC_ERP.exe"
    CreateDirectory "$SMPROGRAMS\SIAC ERP"
    CreateShortcut "$SMPROGRAMS\SIAC ERP\SIAC ERP.lnk" "$INSTDIR\SIAC_ERP.exe"
    CreateShortcut "$SMPROGRAMS\SIAC ERP\Desinstalar.lnk" "$INSTDIR\uninstall.exe"

    ; Registro de Windows
    WriteRegStr HKLM "Software\SIAC ERP" "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\SIAC ERP" "Version" "1.2.1"
    WriteUninstaller "$INSTDIR\uninstall.exe"

    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SIAC ERP" \
        "DisplayName" "SIAC ERP"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SIAC ERP" \
        "UninstallString" '"$INSTDIR\uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SIAC ERP" \
        "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SIAC ERP" \
        "DisplayVersion" "1.2.1"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SIAC ERP" \
        "Publisher" "Mario Felipe Luevano"

SectionEnd

; ============================================================
; SECCION: Desinstalacion
; ============================================================
Section "Desinstalar"
    Delete "$INSTDIR\uninstall.exe"
    RMDir /r "$INSTDIR"
    Delete "$DESKTOP\SIAC ERP.lnk"
    RMDir /r "$SMPROGRAMS\SIAC ERP"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SIAC ERP"
    DeleteRegKey HKLM "Software\SIAC ERP"
SectionEnd
