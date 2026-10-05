@echo off
rem Stops the inkscape-mcp servers started by start.bat.
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" -Stop
