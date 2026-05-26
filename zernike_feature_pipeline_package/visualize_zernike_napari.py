import os
import numpy as np
import tifffile
import napari
import pandas as pd

# Paths (adjust if needed)
BASE_DIR = r'c:\Users\banerjee\Desktop\um1_3d_volume'
TIF_PATH = os.path.join(BASE_DIR, r'docker_cell_detection\F0200_multichannel_cmle_ch04.tif')
SWC_PATH = os.path.join(BASE_DIR, r'neuron_processing\output\custom_crops\zernike_detected_centroids.swc')

def load_swcs(swc_path):
    """Parse a simple SWC file (id type x y z radius parent) and return XYZ coordinates."""
    cols = ['id', 'type', 'x', 'y', 'z', 'r', 'parent']
    df = pd.read_csv(swc_path, sep=r'\s+', comment='#', header=None, names=cols)
    # napari expects (Z, Y, X) order for points in 3‑D
    points = df[['z', 'y', 'x']].values.astype(float)
    return points

def main():
    # Load volume
    print('Loading volume...')
    vol = tifffile.imread(TIF_PATH)
    print(f'Volume shape: {vol.shape}')

    # Load detected centroids
    print('Loading detected centroids...')
    points = load_swcs(SWC_PATH)
    print(f'Loaded {len(points)} centroids')

    # Launch napari viewer
    viewer = napari.Viewer()
    viewer.add_image(vol, name='Channel 04', colormap='gray')
    viewer.add_points(points, size=5, name='Zernike centroids', face_color='red')
    napari.run()

if __name__ == '__main__':
    main()
