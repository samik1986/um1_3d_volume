@echo off
echo ===================================================
echo   Zernike 3D Batch Feature Extraction Pipeline
echo   Created by: Samik Banerjee @ Mitralab @ CSHL
echo ===================================================
cd /d "%~dp0"

:: Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python was not found in PATH!
    echo Attempting to launch/install Python automatically...
    start "" "https://www.python.org/downloads/"
    echo Please install Python and check the "Add Python to PATH" box.
    pause
    exit /b
)

python launcher.py %*
pause
