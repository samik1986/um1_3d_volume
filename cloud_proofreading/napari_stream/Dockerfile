# Base image with NVIDIA CUDA and OpenGL support
FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

# Prevent interactive prompts during apt install
ENV DEBIAN_FRONTEND=noninteractive

# Install core desktop, VNC, and OpenGL requirements
RUN apt-get update && apt-get install -y \
    python3.10 python3-pip python3.10-venv \
    xvfb x11vnc novnc websockify fluxbox \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev \
    virtualgl \
    git wget curl \
    && rm -rf /var/lib/apt/lists/*

# Setup novnc web interface symlink
RUN ln -s /usr/share/novnc/vnc.html /usr/share/novnc/index.html

# Set working directory
WORKDIR /app

# Install Python requirements
# We install standard requirements plus specific Qt bindings for headless GUI
COPY neurite_detection/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt \
    && pip3 install --no-cache-dir pyqt5

# Copy the application code
COPY neurite_detection /app/neurite_detection

# Copy the entrypoint script
COPY cloud_proofreading/napari_stream/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose noVNC port
EXPOSE 8080

# Start the VNC/noVNC server and the application
ENTRYPOINT ["/app/entrypoint.sh"]
