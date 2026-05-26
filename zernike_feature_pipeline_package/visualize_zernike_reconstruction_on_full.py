import os
import sys
import json
import time
import pandas as pd
import numpy as np
import tifffile
import napari

# Import the GPU Filter Bank
from build_zernike_filter_gpu import ZernikeFilterBank

def main():
    print("========================================")
    print("   Zernike 3D Reconstruction Overlay    ")
    print("========================================")
    
    # 1. Configuration
    base_dir = r'c:\Users\banerjee\Desktop\um1_3d_volume'
    tif_path = os.path.join(base_dir, r'docker_cell_detection\F0200_multichannel_cmle_ch04.tif')
    swc_path = os.path.join(base_dir, r'neuron_processing\output\custom_crops\zernike_detected_centroids.swc')
    optimal_keys_path = os.path.join(base_dir, r'neuron_processing\output\custom_crops\optimal_basis_keys.json')
    
    voxel_spacing = (0.5, 0.1102, 0.1102)
    Z_dim, Y_dim, X_dim = 50, 150, 150
    
    # Target cell ID to reconstruct and overlay
    TARGET_CELL_ID = 1  
    
    # 2. Compile Filter Bank
    print("Compiling Zernike Filter Bank on GPU...")
    filter_bank = ZernikeFilterBank(
        optimal_keys_path, 
        voxel_spacing, 
        z_dim=Z_dim, 
        y_dim=Y_dim, 
        x_dim=X_dim
    )
    
    # 3. Load Centroids
    print(f"Loading centroids from {swc_path}")
    cols = ['id', 'type', 'x', 'y', 'z', 'r', 'parent']
    df_centroids = pd.read_csv(swc_path, sep=r'\s+', comment='#', header=None, names=cols)
    
    # Get target centroid
    row = df_centroids.iloc[TARGET_CELL_ID - 1]
    px_x = int(round(row['x']))
    px_y = int(round(row['y']))
    px_z = int(round(row['z']))
    
    z_start = px_z - Z_dim // 2
    z_end   = z_start + Z_dim
    y_start = px_y - Y_dim // 2
    y_end   = y_start + Y_dim
    x_start = px_x - X_dim // 2
    x_end   = x_start + X_dim
    
    # 4. Load full volume
    print(f"Loading full 4GB volume: {tif_path}")
    vol = tifffile.imread(tif_path)
    max_z, max_y, max_x = vol.shape
    
    # 5. Extract Crop (with zero padding if on edge)
    print(f"Extracting Crop for Cell ID {TARGET_CELL_ID} at XYZ: ({px_x}, {px_y}, {px_z})...")
    crop = np.zeros((Z_dim, Y_dim, X_dim), dtype=vol.dtype)
    
    z_s_vol = max(0, z_start)
    z_e_vol = min(max_z, z_end)
    y_s_vol = max(0, y_start)
    y_e_vol = min(max_y, y_end)
    x_s_vol = max(0, x_start)
    x_e_vol = min(max_x, x_end)
    
    z_s_crop = z_s_vol - z_start
    z_e_crop = z_s_crop + (z_e_vol - z_s_vol)
    y_s_crop = y_s_vol - y_start
    y_e_crop = y_s_crop + (y_e_vol - y_s_vol)
    x_s_crop = x_s_vol - x_start
    x_e_crop = x_s_crop + (x_e_vol - x_s_vol)
    
    crop[z_s_crop:z_e_crop, y_s_crop:y_e_crop, x_s_crop:x_e_crop] = vol[z_s_vol:z_e_vol, y_s_vol:y_e_vol, x_s_vol:x_e_vol]
    
    # 6. Extract and Reconstruct
    _, C_vector = filter_bank.extract(crop)
    recon_crop = filter_bank.reconstruct(C_vector)
    
    # 7. Visualization
    print("Opening Napari to show overlay...")
    viewer = napari.Viewer()
    
    # Add full volume (rendered with voxel spacing scale)
    viewer.add_image(vol, name='Original Volume', colormap='gray', scale=voxel_spacing)
    
    # We add the crops with translate to place them exactly where they belong in the full volume
    # Note: translation is in physical units because scale is applied
    translation = (z_start * voxel_spacing[0], 
                   y_start * voxel_spacing[1], 
                   x_start * voxel_spacing[2])
    
    # Add original crop
    viewer.add_image(crop, name='Original Crop Box', colormap='green', 
                     scale=voxel_spacing, translate=translation, blending='additive', opacity=0.3)
                     
    # Add reconstructed crop
    viewer.add_image(recon_crop, name='Zernike Reconstruction', colormap='magma', 
                     scale=voxel_spacing, translate=translation, blending='additive', opacity=1.0)
    
    # Add centroid marker for context
    viewer.add_points(np.array([[px_z, px_y, px_x]]), size=5, name='Cell Centroid', face_color='red', scale=voxel_spacing)
                     
    # Zoom camera to the specific cell
    viewer.camera.center = (px_z * voxel_spacing[0], px_y * voxel_spacing[1], px_x * voxel_spacing[2])
    viewer.camera.zoom = 5.0
    
    napari.run()

if __name__ == '__main__':
    main()
