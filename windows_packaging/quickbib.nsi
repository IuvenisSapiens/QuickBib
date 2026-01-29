; =========================
; QuickBib NSIS Installer
; GUI + Silent (winget-safe)
; =========================

!define APP_NAME "QuickBib"
!define COMPANY "Archisman Panigrahi"
!define VERSION "0.5.1"

; Installer display name shown in the window title and installer UI
Name "${APP_NAME}"
OutFile "${APP_NAME}-Installer-${VERSION}.exe"

; Default to user-level execution (winget requirement)
RequestExecutionLevel user

!include MUI2.nsh
!include nsDialogs.nsh
!include LogicLib.nsh
!include FileFunc.nsh

!insertmacro GetParameters
!insertmacro GetOptions

; -------------------------
; UI configuration
; -------------------------
!define MUI_ICON "..\\assets\\icon\\64x64\\io.github.archisman_panigrahi.QuickBib.ico"
Icon "..\\assets\\icon\\64x64\\io.github.archisman_panigrahi.QuickBib.ico"

; Enable silent installs
SilentInstall silent

Var RADIO_ALL
Var RADIO_USER
Var INSTALL_SCOPE

; -------------------------
; Pages
; -------------------------

Page custom ScopePageCreate ScopePageLeave
Page directory
Page instfiles

; -------------------------
; Initialization
; -------------------------

Function .onInit
  ; Default: current user install
  StrCpy $INSTALL_SCOPE "USER"
  StrCpy $INSTDIR "$LOCALAPPDATA\\Programs\\${APP_NAME}"

  ${GetParameters} $R0

  ; Silent ALLUSERS install
  ${GetOptions} $R0 "/ALLUSERS" $R1
  ${If} $R1 != ""
    StrCpy $INSTALL_SCOPE "ALL"
    StrCpy $INSTDIR "$PROGRAMFILES\\${APP_NAME}"
    Return
  ${EndIf}

  ; Silent CURRENTUSER install (explicit)
  ${GetOptions} $R0 "/CURRENTUSER" $R1
  ${If} $R1 != ""
    StrCpy $INSTALL_SCOPE "USER"
    StrCpy $INSTDIR "$LOCALAPPDATA\\Programs\\${APP_NAME}"
  ${EndIf}
FunctionEnd

; -------------------------
; Scope selection UI
; -------------------------

Function ScopePageCreate
  IfSilent skipScopePage

  nsDialogs::Create 1018
  Pop $0
  ${If} $0 == error
    Abort
  ${EndIf}

  ${NSD_CreateLabel} 0 0 100% 12u "Install scope"
  Pop $R0

  ${NSD_CreateRadioButton} 0 20u 100% 12u "Install for all users (requires admin)"
  Pop $RADIO_ALL

  ${NSD_CreateRadioButton} 0 36u 100% 12u "Install for current user only"
  Pop $RADIO_USER

  ; Default to current user
  ${NSD_SetState} $RADIO_USER 1

  nsDialogs::Show

skipScopePage:
FunctionEnd

Function ScopePageLeave
  IfSilent done

  ${NSD_GetState} $RADIO_ALL $0
  ${If} $0 == 1
    StrCpy $INSTALL_SCOPE "ALL"
    StrCpy $INSTDIR "$PROGRAMFILES\\${APP_NAME}"
  ${Else}
    StrCpy $INSTALL_SCOPE "USER"
    StrCpy $INSTDIR "$LOCALAPPDATA\\Programs\\${APP_NAME}"
  ${EndIf}

done:
FunctionEnd

; -------------------------
; Install section
; -------------------------

Section "Install"
  ${If} $INSTALL_SCOPE == "ALL"
    ; Elevate only when needed
    SetShellVarContext all
    SetOutPath "$PROGRAMFILES\\${APP_NAME}"
  ${Else}
    SetShellVarContext current
    SetOutPath "$LOCALAPPDATA\\Programs\\${APP_NAME}"
  ${EndIf}

  ; Copy application files
  File /r "..\\dist\\QuickBib\\*"
  File "..\\LICENSE"

  ; Create Start Menu shortcut
  CreateDirectory "$SMPROGRAMS\\${APP_NAME}"
  CreateShortCut "$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk" "$INSTDIR\\QuickBib.exe"

  ; Create desktop shortcut
  CreateShortCut "$DESKTOP\\${APP_NAME}.lnk" "$INSTDIR\\QuickBib.exe"

  ; Registry
  ${If} $INSTALL_SCOPE == "ALL"
    WriteRegStr HKLM "Software\\${COMPANY}\\${APP_NAME}" "Install_Dir" "$INSTDIR"
  ${Else}
    WriteRegStr HKCU "Software\\${COMPANY}\\${APP_NAME}" "Install_Dir" "$INSTDIR"
  ${EndIf}

  ; Write Uninstaller
  WriteUninstaller "$INSTDIR\\Uninstall.exe"
SectionEnd

; -------------------------
; Uninstall section
; -------------------------

Section "Uninstall"
  ; Read install dir: prefer HKLM (all-users), fall back to HKCU (current-user)
  ReadRegStr $0 HKLM "Software\\${COMPANY}\\${APP_NAME}" "Install_Dir"
  StrCmp $0 "" 0 +3
    ReadRegStr $0 HKCU "Software\\${COMPANY}\\${APP_NAME}" "Install_Dir"
    StrCmp $0 "" 0 done

  ; Remove shortcuts
  Delete "$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk"
  RMDir "$SMPROGRAMS\\${APP_NAME}"
  Delete "$DESKTOP\\${APP_NAME}.lnk"

  ; Delete files
  RMDir /r "$0"

  ; Remove registry
  DeleteRegKey HKLM "Software\\${COMPANY}\\${APP_NAME}"
  DeleteRegKey HKCU "Software\\${COMPANY}\\${APP_NAME}"

done:
  ; Remove uninstaller
  Delete "$0\\Uninstall.exe"
SectionEnd

