@echo off
echo ========================================================
echo Multilingual Translation AI - Local Model Installer
echo ========================================================
echo.
echo This script will install all required Python packages
echo and download the AI models (approx. 2.5GB total).
echo Please ensure you have a stable internet connection.
echo The download might take several minutes depending on your speed.
echo.
pause

echo.
echo [1/2] Installing Python Dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error installing dependencies. Please check if Python and pip are installed.
    pause
    exit /b %errorlevel%
)

echo.
echo [2/2] Downloading AI Models (this may take a while)...
python verify_llm.py
if %errorlevel% neq 0 (
    echo Error downloading models. Please check your internet connection.
    pause
    exit /b %errorlevel%
)

echo.
echo ========================================================
echo INSTALLATION COMPLETE!
echo The models are now heavily cached on your computer.
echo You can safely run the application completely offline.
echo ========================================================
echo.
pause
