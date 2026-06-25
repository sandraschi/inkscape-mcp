!macro KillFleetProcesses
  DetailPrint "Stopping Inkscape MCP processes..."

  ; Stop-Process (same-user) + taskkill /F /IM (any user).  If the process is
  ; running as SYSTEM or another user, the Rust free_port() function has a UAC
  ; elevation fallback that fires on the next app launch.
  ExecWait 'powershell -NoProfile -Command "Stop-Process -Name inkscape-mcp-backend -Force -ErrorAction SilentlyContinue; Stop-Process -Name inkscape-mcp-native -Force -ErrorAction SilentlyContinue; taskkill /F /IM inkscape-mcp-backend.exe /T; taskkill /F /IM inkscape-mcp-native.exe /T"' $0

  ; NSIS plugin fallback
  !if "${INSTALLMODE}" == "currentUser"
    nsis_tauri_utils::KillProcessCurrentUser "inkscape-mcp-backend.exe"
    Pop $0
    nsis_tauri_utils::KillProcessCurrentUser "inkscape-mcp-native.exe"
    Pop $0
  !else
    nsis_tauri_utils::KillProcess "inkscape-mcp-backend.exe"
    Pop $0
    nsis_tauri_utils::KillProcess "inkscape-mcp-native.exe"
    Pop $0
  !endif

  Sleep 3000
!macroend

!macro UninstallPrevious
  DetailPrint "Checking for previous installation..."
  ; Check current user first, then machine
  !if "${INSTALLMODE}" == "currentUser"
    ReadRegStr $R0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${IDENTIFIER}" "UninstallString"
  !else
    ReadRegStr $R0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${IDENTIFIER}" "UninstallString"
  !endif

  ${If} $R0 != ""
    DetailPrint "Found previous installation at $R0"
    ; Run old uninstaller silently, wait for it
    ExecWait '"$R0" /S' $0
    DetailPrint "Previous uninstall exit code: $0"
    Sleep 1500
  ${EndIf}
!macroend

!macro NSIS_HOOK_PREINSTALL
  !insertmacro KillFleetProcesses
  !insertmacro UninstallPrevious
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  !insertmacro KillFleetProcesses
!macroend
