#!/bin/bash
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

# Automatically launch the requested Napari viewer via VirtualGL (vglrun) for hardware acceleration
if [ "$TOOL_MODE" = "centroids" ]; then
    echo "Launching Centroid Proofreading Tool..."
    vglrun python3 /app/proofreading/launcher.py
else
    echo "Launching Neurite Proofreading Viewer..."
    # By default we open without files, allowing the user to drag and drop inside the VM,
    # or if env vars are provided, we open them directly.
    if [ -z "$INPUT_RAW" ]; then
        vglrun python3 /app/neurite_detection/utils/viewer.py
    else
        vglrun python3 /app/neurite_detection/utils/viewer.py --raw "$INPUT_RAW" --cw "$INPUT_CW" --mask "$INPUT_MASK" --somas "$INPUT_SOMAS"
    fi
fi

# Keep container running
wait
