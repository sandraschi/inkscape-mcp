@echo off
rem inkscape-mcp: install, repair or start. Rerunning is always safe.
rem Flags are forwarded to start.ps1: -Check -Json -Yes -NoStart -Detach -Stop -Restart -BackendOnly -NoBrowser
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" %*
set "RC=%ERRORLEVEL%"
rem Keep the window open on failure when double-clicked, so the error can be read.
if not "%RC%"=="0" if not "%RC%"=="2" (echo %CMDCMDLINE% | find /i "/c" >nul && pause)
exit /b %RC%
