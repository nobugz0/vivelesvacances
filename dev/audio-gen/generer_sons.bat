@echo off
cd /d "%~dp0"
title Marine la maline - generation des sons
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0generer_sons.ps1"
echo.
if errorlevel 1 (
  echo Ca n'a pas marche : copie le message en rouge a Claude.
) else (
  echo Termine. Dis "c'est fait" a Claude.
)
pause
