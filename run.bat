@echo off
setlocal enabledelayedexpansion
title Transly Application Launcher

echo =========================================
echo       Starting Multilingual Translation Application...
echo =========================================

:: Attempt to install requirements
echo Checking dependencies...
:: pip install -r requirements.txt > nul 2>&1

echo Starting the backend server in a separate window...
start "Transly Backend Server" cmd /k "cd backend && python app.py"

echo Waiting for the server to initialize...
:wait_loop
timeout /t 2 /nobreak > nul
curl -s -o nul http://127.0.0.1:8080/status
if %errorlevel% neq 0 (
    echo Server not ready yet. Waiting...
    goto wait_loop
)

echo Server is up and running!
echo Opening browser...
start chrome http://127.0.0.1:8080

echo Done! You can close this launcher window. The server is running in the other window.
pause
