@echo off
set LOGFILE="%~dp0error_log.txt"
echo --- Simulator Start-Check --- > %LOGFILE%
echo Zeit: %date% %time% >> %LOGFILE%

:: Pfade zu Isaac Sim Python und deinem Mock-Server
set PYTHON_EXE="C:\NVIDIA_Isaac_Sim\python.bat"
set SCRIPT_EXE="C:\Bachelorarbeit\OmniMazeRunnerExtensions\omni.mazerunner.ui\omni\mazerunner\ui\mock_server.py"

echo Teste Python-Pfad... >> %LOGFILE%
if not exist %PYTHON_EXE% (
    echo FEHLER: Python unter %PYTHON_EXE% nicht gefunden >> %LOGFILE%
    echo [!] Python-Pfad falsch. Details im Log.
    pause
    exit /b
)

echo Teste Skript-Pfad... >> %LOGFILE%
:: KORREKTUR: Hier stand vorher %SCRIPT_EXE% am Ende der Zeile
if not exist %SCRIPT_EXE% (
    echo FEHLER: Skript unter %SCRIPT_EXE% nicht gefunden >> %LOGFILE%
    echo [!] Skript-Pfad falsch. Details im Log.
    pause
    exit /b
)

echo Starte Mock-Server Prozess...
echo Starte Prozess... >> %LOGFILE%

:: Startet den Server und schreibt Fehlermeldungen (STDERR) ins Logfile
%PYTHON_EXE% %SCRIPT_EXE% 2>> %LOGFILE%

echo.
echo Prozess beendet mit Code %errorlevel% >> %LOGFILE%
echo [INFO] Server beendet (Code: %errorlevel%). Pruefe error_log.txt bei Problemen.
pause