@echo off
setlocal
echo ========================================================
3: echo       Transly AI Model Downloader / Installer
echo ========================================================
echo.
echo This script will download the required AI models for offline use.
echo Target Models:
echo 1. Translation: facebook/m2m100_418M
echo 2. Transcription: openai/whisper-base (with whisper-tiny fallback)
echo.
echo Approximate size: ~2.2 GB
echo.
set /p choice="Do you want to proceed with the download? (y/n): "
if /i "%choice%" neq "y" goto :eof

echo.
echo [1/2] Checking Python dependencies...
pip install transformers torch sentencepiece librosa
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies. Please ensure Python is installed.
    pause
    exit /b %errorlevel%
)

echo.
echo [2/2] Downloading AI Models into local cache...
python verify_llm.py
if %errorlevel% neq 0 (
    echo [ERROR] Failed to download models. Check your internet connection.
    pause
    exit /b %errorlevel%
)

echo.
echo ========================================================
echo SUCCESS!
echo All required models are now cached on this machine.
echo Transly can now be used COMPLETELY OFFLINE.
echo ========================================================
echo.
pause
