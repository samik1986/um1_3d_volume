#!/bin/bash
# entrypoint.sh (napari_stream)
# 
# Author: Samik Banerjee
# Date: June 5, 2026
# GitHub: https://github.com/samik1986/um1_3d_volume
set -e

# Set environment variables for virtual display
export DISPLAY=:99
export RESOLUTION=1920x1080x24

# Start X virtual framebuffer (Xvfb)
echo "Starting Xvfb..."
Xvfb $DISPLAY -screen 0 $RESOLUTION -ac +extension GLX +render -noreset &
sleep 2

# Start lightweight window manager
echo "Starting Fluxbox..."
fluxbox &
sleep 1

# Start x11vnc
echo "Starting x11vnc..."
x11vnc -display $DISPLAY -nopw -forever -shared -bg -xkb

# Start noVNC (websockify) on port 8080 pointing to x11vnc (port 5900)
echo "Starting noVNC on port 8080..."
websockify --web /usr/share/novnc 8080 localhost:5900 &

# Automatically launch the Unified Napari viewer via VirtualGL (vglrun)
echo "Launching Unified Proofreading Viewer..."
CMD="vglrun python3 /app/unified_viewer.py"

if [ -n "$INPUT_RAW" ]; then
    CMD="$CMD --raw \"$INPUT_RAW\""
fi

if [ -n "$INPUT_SKELETONS" ]; then
    CMD="$CMD --skeletons \"$INPUT_SKELETONS\""
fi

if [ -n "$INPUT_CENTROIDS" ]; then
    CMD="$CMD --centroids \"$INPUT_CENTROIDS\""
fi

echo "Running: $CMD"
eval $CMD

# Keep container running
wait
