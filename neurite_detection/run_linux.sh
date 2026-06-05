#!/bin/bash
echo "==========================================="
echo "Neurite Detection Pipeline - 1-Click Runner"
echo "==========================================="

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 could not be found. Please install Python 3.9+"
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "[INFO] Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "[INFO] Activating virtual environment..."
source venv/bin/activate

echo "[INFO] Installing requirements..."
pip install -r requirements.txt

echo "[INFO] Launching the pipeline..."
if [ -z "$1" ]; then
    echo "No input file provided, using default..."
    python run_pipeline.py
else
    echo "Processing file: $1"
    python run_pipeline.py --input "$1"
fi

echo ""
echo "[INFO] Execution finished."
