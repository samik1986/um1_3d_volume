"""
cluster_ch03_zernike.py

1. Take the dapi centers from centroids_DAPI_scaled.swc
2. Compute the Zernike features for F0200_multichannel_cmle_ch03.tif
3. Perform a clustering using K=2
4. Show the visualization of the volume with the clustered cells in Napari

Created by: Samik Banerjee @ Mitralab @ CSHL
"""

import os
import time
import math
import numpy as np
import pandas as pd
import tifffile
import napari
from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans
from build_zernike_filter_gpu import ZernikeFilterBank

def compute_invariants(moments_dict):
    """
    Groups individual moments into the 54 rotationally invariant shells F_nl.
    """
    shells = {}
    for (n, l, m), C_val in moments_dict.items():
        if (n, l) not in shells:
            shells[(n, l)] = 0.0
        shells[(n, l)] += abs(C_val)**2
    invariants = {f"F_{n}_{l}": math.sqrt(energy) for (n, l), energy in shells.items()}
    return invariants

def main():
    print("==================================================")
    print("   Zernike ch03 Extraction & K=2 Clustering       ")
    print("   Created by: Samik Banerjee @ Mitralab @ CSHL  ")
    print("==================================================")
    
    # 1. Setup paths
    base_dir = r'c:\Users\banerjee\Desktop\um1_3d_volume'
    tif_path = os.path.join(base_dir, r'docker_cell_detection\F0200_multichannel_cmle_ch03.tif')
    swc_path = os.path.join(base_dir, r'docker_cell_detection\centroids_DAPI_scaled.swc')
    optimal_keys_path = os.path.join(base_dir, r'neuron_processing\output\custom_crops\optimal_basis_keys.json')
    
    out_features = os.path.join(base_dir, r'neuron_processing\output\custom_crops\zernike_features_ch03.csv')
    
    voxel_spacing = (0.5, 0.1102, 0.1102)
    Z_dim, Y_dim, X_dim = 50, 150, 150
    
    # 2. Compile Filter Bank
    filter_bank = ZernikeFilterBank(
        optimal_keys_path, 
        voxel_spacing, 
        z_dim=Z_dim, 
        y_dim=Y_dim, 
        x_dim=X_dim
    )
    
    # 3. Load full 4GB image
    print(f"\nLoading ch03 volume: {tif_path}")
    vol = tifffile.imread(tif_path)
    max_z, max_y, max_x = vol.shape
    
    # 4. Load Centroids
    print(f"Loading centroids from {swc_path}")
    df_centroids = pd.read_csv(swc_path, sep=' ', comment='#', header=None, 
                               names=['id', 'type', 'x', 'y', 'z', 'r', 'p'])
    
    num_cells = len(df_centroids)
    print(f"Found {num_cells} cells. Extracting features on ch03...")
    
    features_list = []
    coords_phys = []
    
    # Run batch extraction
    batch_start = time.time()
    for index, row in df_centroids.iterrows():
        c_id = int(row['id'])
        px_z = int(round(row['z'] / voxel_spacing[0]))
        px_y = int(round(row['y'] / voxel_spacing[1]))
        px_x = int(round(row['x'] / voxel_spacing[2]))
        
        # Save physical coordinates for Napari Point layers
        coords_phys.append([row['z'], row['y'], row['x']])
        
        # Calculate bounding box bounds
        z_start = px_z - Z_dim // 2
        z_end   = z_start + Z_dim
        y_start = px_y - Y_dim // 2
        y_end   = y_start + Y_dim
        x_start = px_x - X_dim // 2
        x_end   = x_start + X_dim
        
        # Extract crop with zero-padding boundary conditions
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
        
        if z_e_vol > z_s_vol and y_e_vol > y_s_vol and x_e_vol > x_s_vol:
            crop[z_s_crop:z_e_crop, y_s_crop:y_e_crop, x_s_crop:x_e_crop] = vol[z_s_vol:z_e_vol, y_s_vol:y_e_vol, x_s_vol:x_e_vol]
            
        moments, _ = filter_bank.extract(crop)
        inv = compute_invariants(moments)
        inv['cell_id'] = c_id
        features_list.append(inv)
        
        if (index + 1) % 100 == 0:
            print(f"Processed {index + 1}/{num_cells} cells...")
            
    print(f"Extraction complete! Processed {num_cells} cells in {time.time() - batch_start:.2f}s.")
    
    df_features = pd.DataFrame(features_list)
    df_features.to_csv(out_features, index=False)
    print(f"Features saved to {out_features}")
    
    # 5. K-Means clustering (K=2)
    print("\nPerforming K-Means Clustering (K=2) on shell invariants...")
    feature_cols = [c for c in df_features.columns if c.startswith('F_')]
    X = df_features[feature_cols].values
    
    # Normalize features to prevent scale bias
    from sklearn.preprocessing import StandardScaler
    X_scaled = StandardScaler().fit_transform(X)
    
    kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X_scaled)
    
    df_centroids['cluster'] = cluster_labels
    coords_phys = np.array(coords_phys)
    
    # Separate clusters
    cluster_0_coords = coords_phys[cluster_labels == 0]
    cluster_1_coords = coords_phys[cluster_labels == 1]
    
    print(f"Cluster 0: {len(cluster_0_coords)} cells (Red)")
    print(f"Cluster 1: {len(cluster_1_coords)} cells (Blue)")
    
    # 6. Napari Visualization
    print("\nLaunching Napari Viewer...")
    viewer = napari.Viewer()
    
    # Display volume
    viewer.add_image(
        vol, 
        name='Volume ch03', 
        scale=voxel_spacing, 
        blending='additive', 
        colormap='gray'
    )
    
    # Display Cluster 0 in Red
    viewer.add_points(
        cluster_0_coords,
        name='Cluster 0 (Red)',
        size=10.0,
        face_color='red',
        border_color='white',
        blending='translucent'
    )
    
    # Display Cluster 1 in Blue
    viewer.add_points(
        cluster_1_coords,
        name='Cluster 1 (Blue)',
        size=10.0,
        face_color='blue',
        border_color='white',
        blending='translucent'
    )
    
    napari.run()

if __name__ == '__main__':
    main()
