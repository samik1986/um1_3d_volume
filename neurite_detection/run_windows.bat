@echo off
echo ===========================================
echo Neurite Detection Pipeline - 1-Click Runner
echo ===========================================

REM Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH. Please install Python 3.9+
    pause
    exit /b
)

REM Create virtual environment if it doesn't exist
IF NOT EXIST "venv" (
    echo [INFO] Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install dependencies
echo [INFO] Installing requirements...
pip install -r requirements.txt

REM Run the pipeline
echo [INFO] Launching the pipeline...
IF "%~1"=="" (
    echo No input file provided, using default...
    python run_pipeline.py
) ELSE (
    echo Processing file: %~1
    python run_pipeline.py --input "%~1"
)

echo.
echo [INFO] Execution finished.
pause
