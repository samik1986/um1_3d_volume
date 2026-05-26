#!/bin/bash
# Cross-platform bash runner for macOS and Linux systems
# Created by: Samik Banerjee @ Mitralab @ CSHL
echo "==================================================="
echo "  3D Centroid Proofreader Widget                   "
echo "  Created by: Samik Banerjee @ Mitralab @ CSHL     "
echo "==================================================="
# Navigate to script's directory
cd "$(dirname "$0")"

# Find a valid python command
if command -v python3 &>/dev/null; then
    python3 launcher.py
elif command -v python &>/dev/null; then
    python launcher.py
else
    echo "Error: Python is not installed or not found in PATH."
    exit 1
fi
