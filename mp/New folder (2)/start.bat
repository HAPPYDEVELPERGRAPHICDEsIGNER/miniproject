@echo off
title AI Software Engineering Copilot
cd /d "%~dp0"

echo ===================================================
echo   AI Software Engineering Copilot - Starting Up
echo ===================================================
echo.
echo Opening browser at http://127.0.0.1:8000 ...
start http://127.0.0.1:8000
echo.
echo Server running. Keep this window open while using the app.
echo Press CTRL+C in this window to stop the server.
echo.

".\venv\Scripts\python.exe" -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
pause
