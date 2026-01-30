; NSIS script to package the PyInstaller 'dist/QuickBib' output into an installer.
; This script assumes the build step produces a folder 'dist\QuickBib' with QuickBib.exe

!define APP_NAME "QuickBib"
!define COMPANY "Archisman Panigrahi"
!define VERSION "0.5.2"

; Installer display name shown in the window title and installer UI
Name "${APP_NAME}"

; Default execution level: user (no UAC unless needed)
RequestExecutionLevel user

!include nsDialogs.nsh
!include LogicLib.nsh
!include FileFunc.nsh

; Use Modern UI 2 so we can set the installer UI icon to the application icon
!define MUI_ICON "..\\assets\\icon\\64x64\\io.github.archisman_panigrahi.QuickBib.ico"
!include MUI2.nsh

Var RADIO_ALL
Var RADIO_USER
Var INSTALL_SCOPE
Var CMD_ALLUSERS
Var CMD_CURRENTUSER

; The NSIS script lives in the `windows_packaging` directory. Paths in this script
; are resolved relative to the script's location, so reference files in the repo root
; using a parent-directory prefix.
Icon "..\\assets\\icon\\64x64\\io.github.archisman_panigrahi.QuickBib.ico"

OutFile "${APP_NAME}-Installer-${VERSION}.exe"
InstallDir "$PROGRAMFILES\\${APP_NAME}"

; Custom page to select installation scope: All users (Program Files) or Current user (LocalAppData)
Page custom ScopePageCreate ScopePageLeave
Page directory
Page instfiles

SetCompress off

Function .onInit
  ${GetParameters} $R0

  ClearErrors
  ${GetOptions} $R0 "/ALLUSERS" $CMD_ALLUSERS
  ${GetOptions} $R0 "/CURRENTUSER" $CMD_CURRENTUSER

  IfSilent 0 interactive_mode

  ; Silent install handling
  StrCmp $CMD_ALLUSERS "" 0 silent_all
  StrCmp $CMD_CURRENTUSER "" 0 silent_user

  ; Default silent install = CURRENTUSER
  Goto silent_user

silent_all:
  StrCpy $INSTALL_SCOPE "ALL"
  StrCpy $INSTDIR "$PROGRAMFILES\\${APP_NAME}"
  SetShellVarContext all
  Goto done

silent_user:
  StrCpy $INSTALL_SCOPE "USER"
  StrCpy $INSTDIR "$LOCALAPPDATA\\Programs\\${APP_NAME}"
  SetShellVarContext current
  Goto done

interactive_mode:
  ; Default interactive install = ALL users
  StrCpy $INSTALL_SCOPE "ALL"
  StrCpy $INSTDIR "$PROGRAMFILES\\${APP_NAME}"
  SetShellVarContext all

done:
FunctionEnd

Function ScopePageCreate
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

  ; Default to All users in GUI
  ${NSD_SetState} $RADIO_ALL 1

  nsDialogs::Show
FunctionEnd

Function ScopePageLeave
  ${NSD_GetState} $RADIO_ALL $0
  ${If} $0 == 1
    StrCpy $INSTALL_SCOPE "ALL"
    StrCpy $INSTDIR "$PROGRAMFILES\\${APP_NAME}"
    SetShellVarContext all
  ${Else}
    StrCpy $INSTALL_SCOPE "USER"
    StrCpy $INSTDIR "$LOCALAPPDATA\\Programs\\${APP_NAME}"
    SetShellVarContext current
  ${EndIf}
FunctionEnd

Section "Install"

  ; Debug: Log the install scope and directory
  DetailPrint "INSTALL_SCOPE: $INSTALL_SCOPE"
  DetailPrint "INSTDIR (before): $INSTDIR"

  ; Enforce install dir (MUI may override INSTDIR in silent mode)
  StrCmp $INSTALL_SCOPE "USER" 0 +3
    StrCpy $INSTDIR "$LOCALAPPDATA\\Programs\\${APP_NAME}"
    SetShellVarContext current
    Goto +4
  StrCpy $INSTDIR "$PROGRAMFILES\\${APP_NAME}"
  SetShellVarContext all

  DetailPrint "INSTDIR (after): $INSTDIR"
  DetailPrint "Starting file copy..."

  SetOutPath "$INSTDIR"

  ; Copy all files from the PyInstaller output (dist is at repo root, so step up one dir)
  File /r "..\\dist\\QuickBib\\*"
  DetailPrint "File copy completed"

  ; Include repository LICENSE in the installed files so users can view the license
  File "..\\LICENSE"

  ; Create Start Menu shortcut
  CreateDirectory "$SMPROGRAMS\\${APP_NAME}"
  CreateShortCut "$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk" "$INSTDIR\\QuickBib.exe"

  ; Create desktop shortcut
  CreateShortCut "$DESKTOP\\${APP_NAME}.lnk" "$INSTDIR\\QuickBib.exe"

  ; Write install location for uninstaller
  StrCmp $INSTALL_SCOPE "ALL" 0 +3
    WriteRegStr HKLM "Software\\${COMPANY}\\${APP_NAME}" "Install_Dir" "$INSTDIR"
    Goto +2
  WriteRegStr HKCU "Software\\${COMPANY}\\${APP_NAME}" "Install_Dir" "$INSTDIR"

  ; Write Uninstaller
  WriteUninstaller "$INSTDIR\\Uninstall.exe"
SectionEnd

Section "Uninstall"
  ; Read install dir: prefer HKLM (all-users), fall back to HKCU (current-user)
  ReadRegStr $0 HKLM "Software\\${COMPANY}\\${APP_NAME}" "Install_Dir"
  StrCmp $0 "" 0 +3
    ReadRegStr $0 HKCU "Software\\${COMPANY}\\${APP_NAME}" "Install_Dir"
    StrCmp $0 "" 0 +2
      Goto done

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
  Delete "$0\\Uninstall.exe"
SectionEnd

