@echo off
where pwsh >nul 2>nul
if errorlevel 1 (
  echo Install PowerShell 7.4 or later. Read docs\LOCAL_REQUIREMENTS.md.
  exit /b 1
)
pwsh -NoProfile -File "%~dp0Run-Kairnfall-Dev.ps1"
exit /b %errorlevel%
