@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-Kairnfall.ps1"
if errorlevel 1 (
  echo.
  echo Kairnfall did not start. Read the message above.
  pause
)
endlocal
