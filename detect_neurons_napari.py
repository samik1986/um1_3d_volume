"""
detect_neurons_napari.py

Author: Samik Banerjee
Date: May 8, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

3D Neuron detection and visualization using Napari and Frangi filter.
"""

import napari
import tifffile
import numpy as np
import os
from skimage.filters import frangi
from skimage.morphology import skeletonize
from skimage import exposure
import time

def detect_neurons_napari():
    input_file = 'docker_cell_detection/F0200_multichannel_cmle_ch03.tif'
    if not os.path.exists(input_file):
        # Try root
        input_file = 'F0200_multichannel_cmle_ch03.tif'
        
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    print(f"Opening volume: {input_file}")
    # Use memory mapping to avoid loading 4GB into RAM immediately
    with tifffile.TiffFile(input_file) as tif:
        volume_mmap = tif.asarray(out='memmap')
    
    print(f"Volume mapped. Shape: {volume_mmap.shape}")
    
    # Process a subvolume for speed and memory safety
    # Let's take a central 512x512 subvolume for all slices
    z, h, w = volume_mmap.shape
    crop_size = 512
    y_start, x_start = (h - crop_size)//2, (w - crop_size)//2
    y_end, x_end = y_start + crop_size, x_start + crop_size
    
    print(f"Extracting subvolume: [{y_start}:{y_end}, {x_start}:{x_end}]...")
    subvolume = volume_mmap[:, y_start:y_end, x_start:x_end].astype(np.float32)
    
    # Pre-processing: Normalize and enhance contrast
    print("Pre-processing subvolume...")
    subvolume = exposure.rescale_intensity(subvolume, in_range=(0, 500), out_range=(0, 1))
    
    print("Applying 3D Frangi filter (Axon/Dendrite detection)...")
    start_time = time.time()
    # Sigmas correspond to the radius of neurons in pixels
    # Neuron radius is typically 1-3 pixels at this resolution
    vesselness = frangi(subvolume, sigmas=[1, 2, 4], black_ridges=False)
    print(f"Frangi complete in {time.time() - start_time:.2f} seconds.")
    
    # Threshold vesselness to get binary mask
    # Vesselness values are typically low, let's use a percentile
    thresh = np.percentile(vesselness, 99)
    binary_neurons = vesselness > thresh
    
    print("Skeletonizing detections...")
    skeleton = skeletonize(binary_neurons)
    
    print("Opening Napari Viewer...")
    viewer = napari.Viewer(title="3D Neuron Detection - F0200 ch03")
    
    # Add raw volume
    viewer.add_image(
        subvolume, 
        name='Raw Volume (Subvolume)', 
        colormap='gray', 
        blending='additive'
    )
    
    # Add Vesselness map
    viewer.add_image(
        vesselness, 
        name='Vesselness Map', 
        colormap='hot', 
        blending='additive',
        visible=False
    )
    
    # Add skeletonized neurons
    # Convert skeleton to points for better 3D visualization or use labels
    viewer.add_labels(
        skeleton.astype(int), 
        name='Detected Neurons (Skeleton)'
    )
    
    print("Visualization ready. Inspect the 'Detected Neurons (Skeleton)' layer.")
    napari.run()

if __name__ == '__main__':
    detect_neurons_napari()
