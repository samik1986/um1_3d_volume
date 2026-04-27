import napari
import tifffile
import pandas as pd
import numpy as np
import os

def load_swc(filename):
    """Loads centroids from an SWC file."""
    try:
        # SWC format: id type x y z radius parent
        # Skip comments
        data = pd.read_csv(filename, sep=' ', comment='#', header=None, 
                          names=['id', 'type', 'x', 'y', 'z', 'r', 'p'])
        return data
    except Exception as e:
        print(f"Error loading SWC: {e}")
        return None

def visualize_napari():
    input_file = 'F0200_multichannel_cmle_ch04.tif'
    swc_file = 'centroids.swc'
    
    if not os.path.exists(input_file):
        input_file = os.path.join('..', input_file)
    if not os.path.exists(swc_file):
        swc_file = os.path.join('..', swc_file)
    
    if not os.path.exists(input_file):
        print(f"File {input_file} not found.")
        return

    print("Loading volume...")
    # Use memory mapping for performance with large TIFFs
    volume = tifffile.imread(input_file)
    
    print("Loading SWC data...")
    centroids_df = load_swc(swc_file)
    
    print("Opening Napari Viewer...")
    viewer = napari.Viewer(title="3D Cell Detection Viewer - um1_3d_volume")
    
    # Add volume layer
    # Bio-imaging standard is often (z, y, x)
    viewer.add_image(volume, name='Cell Volume', colormap='gray', blending='additive')
    
    # Add centroids layer
    if centroids_df is not None:
        # Note: SWC x,y,z usually corresponds to V index as [z, y, x] in napari for 3D
        # Coordinates in SWC are x, y, z. We need to pass them as (z, y, x) to napari
        points = centroids_df[['z', 'y', 'x']].values
        viewer.add_points(
            points, 
            name='Centroids', 
            size=15, 
            face_color='red', 
            border_color='white',
            symbol='disc',
            n_dimensional=True # Allow points to be seen across slices if needed
        )
    
    print("Napari is now open. Inspect the volume and centroids.")
    napari.run()

if __name__ == '__main__':
    visualize_napari()
