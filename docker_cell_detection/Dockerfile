# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for imaging libraries
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY docker_cell_detection/requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the python scripts into the container
COPY cell_detection_py/ /app/cell_detection_py/

# Create a data directory for mounting
RUN mkdir /data

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command to run the detection script
# Usage: docker run -v /path/to/data:/data cell-detection --input /data/volume.tif --output /data/centroids.swc
ENTRYPOINT ["python", "cell_detection_py/run_centroids.py"]
CMD ["--input", "/data/F0200_multichannel_cmle_ch04.tif", "--output", "/data/centroids.swc"]
