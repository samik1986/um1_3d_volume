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
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy all python scripts from the current folder into the container
COPY . /app/

# Create a data directory for mounting
RUN mkdir /data

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command to run the pipeline
# Usage: docker run -v /path/to/data:/data cell-detection --dapi /data/ch04.tif --fp /data/ch03.tif
ENTRYPOINT ["python", "run_pipeline.py"]
CMD ["--dapi", "/data/F0200_multichannel_cmle_ch04.tif", "--fp", "/data/F0200_multichannel_cmle_ch03.tif"]
