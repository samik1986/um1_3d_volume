@echo off
echo =================================================
echo ☁️ Deploying Secure Napari Cloud Proofreading UI
echo =================================================

IF NOT EXIST ".env" (
    echo [WARNING] .env file not found! Copying from .env.example...
    copy .env.example .env
    echo Please open the new .env file and fill in your Google Client ID/Secret before running this script again!
    pause
    exit /b
)

echo [INFO] Pulling the latest Docker images from Docker Hub...
docker-compose pull

echo [INFO] Launching the Cloud Proofreading stack...
docker-compose up -d

echo.
echo ✅ Deployment Successful!
echo Navigate to http://localhost (or your VM's IP address) in your web browser to access the proofreading UI.
pause
