@echo off
setlocal

echo =======================================================
echo Neurite & Soma Extraction Pipeline
echo =======================================================
echo.
echo Installing requirements...
python -m pip install --user -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install requirements! Please check your python/pip installation.
    exit /b %ERRORLEVEL%
)

echo.
echo Launching Pipeline...
python main.py %*

endlocal
