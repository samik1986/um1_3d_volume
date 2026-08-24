#!/bin/bash

echo "======================================================="
echo "Neurite & Soma Extraction Pipeline"
echo "======================================================="
echo ""
echo "Installing requirements..."
python3 -m pip install --user -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install requirements! Please check your python/pip installation."
    exit 1
fi

echo ""
echo "Launching Pipeline..."
python3 main.py "$@"
