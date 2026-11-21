@echo off
REM Double-click to start ALERTIFY and open it in your browser.
REM Close this window (or press Ctrl+C) to stop the server.
title ALERTIFY server
cd /d "%~dp0"

REM If ALERTIFY is already running, just open the browser.
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if %errorlevel%==0 (
    start "" http://127.0.0.1:5000
    exit /b
)

REM Open the browser a few seconds after the server starts.
start "" /b powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep 3; Start-Process 'http://127.0.0.1:5000'"
echo Starting ALERTIFY at http://127.0.0.1:5000  (close this window to stop it)
python app.py
pause
