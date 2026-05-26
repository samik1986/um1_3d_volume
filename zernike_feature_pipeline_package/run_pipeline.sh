#!/bin/bash
# Cross-platform bash runner for macOS and Linux systems
# Created by: Samik Banerjee @ Mitralab @ CSHL
echo "==================================================="
echo "  Zernike 3D Batch Feature Extraction Pipeline     "
echo "  Created by: Samik Banerjee @ Mitralab @ CSHL     "
echo "==================================================="
# Navigate to script's directory
cd "$(dirname "$0")"

# Find a valid python command, otherwise guide the user
if command -v python3 &>/dev/null; then
    python3 launcher.py "$@"
elif command -v python &>/dev/null; then
    python launcher.py "$@"
else
    echo "Error: Python is not installed or not found in PATH."
    echo "Opening Python downloads page..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "https://www.python.org/downloads/"
    else
        xdg-open "https://www.python.org/downloads/"
    fi
    exit 1
fi
