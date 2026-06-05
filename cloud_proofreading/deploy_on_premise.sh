#!/bin/bash
echo "================================================="
echo "🏢 Deploying On-Premise Napari Proofreading UI"
echo "================================================="

if [ ! -f .env ]; then
    echo "[INFO] .env file not found. Falling back to default settings..."
fi

echo "[INFO] Launching the Proofreading stack on port 8080..."
docker-compose -f docker-compose.onprem.yml up -d

echo ""
echo "✅ Deployment Successful!"
echo "Navigate to http://<YOUR_LOCAL_SERVER_IP>:8080 in your web browser (e.g. from any laptop on your internal network/VPN) to access the proofreading UI."
