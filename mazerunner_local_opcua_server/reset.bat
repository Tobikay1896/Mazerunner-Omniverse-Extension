@echo off
set "ISAAC_PATH=C:\NVIDIA_Isaac_Sim"
set "EXE=isaac-sim.bat"

echo Starte NVIDIA Isaac Sim mit --reset-user...
cd /d "%ISAAC_PATH%"

if exist "%EXE%" (
    call "%EXE%" --reset-user
) else (
    echo FEHLER: Die Datei %EXE% wurde unter %ISAAC_PATH% nicht gefunden.
    pause
)