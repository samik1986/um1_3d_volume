"""
visualize_swc_volume.py (neuron_detection)

Author: Samik Banerjee
Date: May 8, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

Visualize SWC files overlaid on the raw 3D volume in Napari. 
Handles the conversion of SWC parent-child relations into visualization paths.
"""

import napari
import tifffile
import pandas as pd
import numpy as np
import os

def load_swc_segments(swc_file):
    """
    Parses an SWC file and returns a list of line segments (paths) 
    connecting each node to its parent, formatted for Napari's Paths layer.
    """
    print(f"Loading SWC data from {swc_file}...")
    try:
        # Standard SWC: id type x y z radius parent_id
        df = pd.read_csv(swc_file, sep=' ', comment='#', header=None,
                         names=['id', 'type', 'x', 'y', 'z', 'r', 'pid'])
        
        # Build a lookup dictionary for coordinates: ID -> (Z, Y, X)
        node_coords = {}
        for _, row in df.iterrows():
            node_coords[row['id']] = (row['z'], row['y'], row['x'])
            
        paths = []
        for _, row in df.iterrows():
            pid = row['pid']
            # If it has a valid parent, create a line segment
            if pid != -1 and pid in node_coords:
                parent_coord = node_coords[pid]
                current_coord = (row['z'], row['y'], row['x'])
                paths.append([parent_coord, current_coord])
                
        print(f"Extracted {len(paths)} line segments from SWC.")
        return paths
        
    except Exception as e:
        print(f"Error loading SWC: {e}")
        return []

def main():
    # 1. Paths
    volume_path = '../docker_cell_detection/F0200_multichannel_cmle_ch03.tif'
    swc_path = 'full_volume_stitched.swc'
    
    # Fallbacks in case script is run from a different directory
    if not os.path.exists(volume_path):
        volume_path = 'docker_cell_detection/F0200_multichannel_cmle_ch03.tif'
    if not os.path.exists(volume_path):
        volume_path = 'F0200_multichannel_cmle_ch03.tif'
        
    if not os.path.exists(swc_path):
        swc_path = 'neuron_detection/full_volume_stitched.swc'

    if not os.path.exists(volume_path):
        print(f"Error: Volume file not found at {volume_path}")
        return
        
    if not os.path.exists(swc_path):
        print(f"Error: SWC file not found at {swc_path}")
        return

    # 2. Load Volume (Memory Mapped to save RAM)
    print(f"Loading 3D volume from {volume_path}...")
    try:
        vol_mmap = tifffile.imread(volume_path, out='memmap')
        print(f"Volume loaded. Shape: {vol_mmap.shape}")
    except Exception as e:
        print(f"Error loading volume: {e}")
        return
        
    # 3. Load SWC
    paths = load_swc_segments(swc_path)
    
    # 4. Launch Napari
    print("\nLaunching Napari Viewer...")
    viewer = napari.Viewer(title="Independent SWC / Volume Viewer")
    
    # Add volume
    viewer.add_image(
        vol_mmap, 
        name='Raw Volume', 
        colormap='gray', 
        blending='translucent'
    )
    
    # Add SWC Paths
    if paths:
        viewer.add_shapes(
            paths, 
            shape_type='path', 
            edge_color='red', 
            edge_width=2, 
            name='SWC Neurons', 
            ndim=3
        )
        
    print("Napari is running. Close the window to exit.")
    napari.run()

if __name__ == '__main__':
    main()
