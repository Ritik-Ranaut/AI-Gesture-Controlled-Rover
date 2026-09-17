@echo off
title STAIROVER Controller Launcher
echo ========================================================
echo  STAIROVER: Hand Gesture Controlled Stair-Climbing Rover
echo ========================================================
echo.

:: Set working directory to project root
cd /d "%~dp0"

echo [1/2] Starting Python Gesture Recognition Service on port 8001...
start "STAIROVER Gesture Service" cmd /k "cd gesture-service && python -u app.py"

timeout /t 2 /nobreak >nul

echo [2/2] Starting React Mission Control Dashboard on port 5173...
start "STAIROVER Frontend Dashboard" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================================
echo  System is booting up!
echo  Dashboard: http://localhost:5173
echo  Backend:   http://localhost:8001
echo ========================================================
echo.
pause
