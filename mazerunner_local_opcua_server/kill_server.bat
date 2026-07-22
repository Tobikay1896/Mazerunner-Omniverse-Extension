@echo off
echo Beende alle OPC UA Prozesse...
taskkill /f /im python.exe /t
echo Port 4840 wurde zwangsgeräumt.
pause