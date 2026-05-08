"""
visualize_napari_csv.py

Author: Samik Banerjee
Date: May 8, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

Visualize CSV point data (e.g., cell barcodes) overlaid on a 3D TIFF volume using Napari.
"""

import napari
import tifffile
import pandas as pd
import numpy as np
import os

def load_csv_points(filename):
    """Loads points from a CSV file (x,y,z,gene)."""
    try:
        data = pd.read_csv(filename)
        return data
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None

def visualize_napari_csv():
    input_file = 'FP.tif'
    csv_file = 'barcode.csv'
    
    if not os.path.exists(input_file):
        print(f"File {input_file} not found.")
        return

    print(f"Loading volume from {input_file}...")
    # Use memory mapping for performance with large TIFFs
    volume = tifffile.imread(input_file)
    print(f"Volume loaded. Shape: {volume.shape}")
    
    print(f"Loading CSV data from {csv_file}...")
    points_df = load_csv_points(csv_file)
    
    print("Opening Napari Viewer...")
    viewer = napari.Viewer(title="3D Cell Detection Viewer - um1_3d_volume (CSV)")
    
    # Add volume layer
    # Bio-imaging standard is often (z, y, x)
    viewer.add_image(volume, name='Cell Volume', colormap='gray', blending='additive')
    
    # Add points layer
    if points_df is not None:
        # Coordinates in CSV are x, y, z. We need to pass them as (z, y, x) to napari
        points = points_df[['z', 'y', 'x']].values
        
        # Prepare properties for coloring if 'gene' exists
        props = {'gene': points_df['gene']} if 'gene' in points_df.columns else None
        
        viewer.add_points(
            points, 
            name='Barcodes', 
            size=10, 
            border_color='white',
            symbol='disc',
            n_dimensional=True,
            properties=props,
            face_color_cycle=['cyan', 'magenta', 'yellow', 'red', 'green', 'blue'],
            face_color='gene' if props else 'red'
        )
    
    print("Napari is now open. Inspect the volume and barcodes.")
    napari.run()

if __name__ == '__main__':
    visualize_napari_csv()
