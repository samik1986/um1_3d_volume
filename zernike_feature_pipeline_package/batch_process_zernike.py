import os
import time
import math
import numpy as np
import cupy as cp
import tifffile
import pandas as pd
from scipy.spatial.distance import cdist

# Import the Filter Bank class
from build_zernike_filter_gpu import ZernikeFilterBank

def compute_invariants(moments_dict):
    """
    Groups individual moments into the 54 rotationally invariant shells F_nl.
    """
    shells = {}
    for (n, l, m), C_val in moments_dict.items():
        if (n, l) not in shells:
            shells[(n, l)] = 0.0
        # Energy sum
        shells[(n, l)] += abs(C_val)**2
        
    # Return sqrt of energy sum (F_nl)
    invariants = {f"F_{n}_{l}": math.sqrt(energy) for (n, l), energy in shells.items()}
    return invariants

def main():
    print("========================================")
    print("   Zernike 3D Batch Feature Extraction  ")
    print("========================================")
    start_total = time.time()
    
    # 1. Configuration
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # The full 4GB image sits outside the package folder for storage efficiency
    base_dir = os.path.dirname(script_dir)
    tif_path = os.path.join(base_dir, r'docker_cell_detection\F0200_multichannel_cmle_ch04.tif')
    
    # Internal package relative data paths
    swc_path = os.path.join(script_dir, 'data', 'centroids_DAPI_scaled.swc')
    optimal_keys_path = os.path.join(script_dir, 'data', 'optimal_basis_keys.json')
    
    out_features = os.path.join(script_dir, 'data', 'zernike_features_dapi.csv')
    out_neighbors = os.path.join(script_dir, 'data', 'nearest_neighbors.csv')
    
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
    
    # 3. Load full 4GB image (Memory Mapped for safety, or direct)
    print(f"\nLoading full 4GB volume: {tif_path}")
    vol = tifffile.imread(tif_path)
    max_z, max_y, max_x = vol.shape
    
    # 4. Load Centroids
    print(f"Loading centroids from {swc_path}")
    df_centroids = pd.read_csv(swc_path, sep=' ', comment='#', header=None, 
                               names=['id', 'type', 'x', 'y', 'z', 'r', 'p'])
    
    num_cells = len(df_centroids)
    print(f"Found {num_cells} cells. Beginning extraction pipeline...")
    
    features_list = []
    cell_ids = []
    
    batch_start = time.time()
    for index, row in df_centroids.iterrows():
        c_id = int(row['id'])
        # In scaled SWC, coordinates are physical coordinates (microns):
        # We divide by the voxel spacing to find pixel indices!
        # voxel_spacing = (Z=0.5, Y=0.1102, X=0.1102)
        px_z = int(round(row['z'] / voxel_spacing[0]))
        px_y = int(round(row['y'] / voxel_spacing[1]))
        px_x = int(round(row['x'] / voxel_spacing[2]))
        
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
        
        # Only populate if valid volume
        if z_e_vol > z_s_vol and y_e_vol > y_s_vol and x_e_vol > x_s_vol:
            crop[z_s_crop:z_e_crop, y_s_crop:y_e_crop, x_s_crop:x_e_crop] = vol[z_s_vol:z_e_vol, y_s_vol:y_e_vol, x_s_vol:x_e_vol]
            
        # INSTANT EXTRACTION
        # The Filter Bank method returns (moments, C_vector). We suppress print inside.
        moments, _ = filter_bank.extract(crop)
        
        # Compute invariants
        inv = compute_invariants(moments)
        
        # Format as row
        inv['cell_id'] = c_id
        inv['x'] = px_x
        inv['y'] = px_y
        inv['z'] = px_z
        features_list.append(inv)
        cell_ids.append(c_id)
        
        if (index + 1) % 50 == 0:
            print(f"Processed {index + 1}/{num_cells} cells...")
            
    print(f"\nExtraction complete! Processed {num_cells} cells in {time.time() - batch_start:.2f}s.")
    
    # 5. Compile Feature Matrix
    df_features = pd.DataFrame(features_list)
    # Move id, x, y, z to front
    cols = ['cell_id', 'x', 'y', 'z'] + [c for c in df_features.columns if c not in ['cell_id', 'x', 'y', 'z']]
    df_features = df_features[cols]
    
    print(f"Saving feature matrix (Shape: {df_features.shape}) to {out_features}")
    df_features.to_csv(out_features, index=False)
    
    # 6. Pairwise Nearest Neighbors
    print("Computing Morphological Similarity Matrix...")
    # Extract only the 54 shape features
    feature_matrix = df_features.drop(columns=['cell_id', 'x', 'y', 'z']).values
    
    # Compute Euclidean distance matrix
    dist_matrix = cdist(feature_matrix, feature_matrix, metric='euclidean')
    
    # Set diagonal to infinity so a cell isn't its own nearest neighbor
    np.fill_diagonal(dist_matrix, np.inf)
    
    # Find nearest neighbor for each cell
    nearest_idx = np.argmin(dist_matrix, axis=1)
    nearest_dists = np.min(dist_matrix, axis=1)
    
    df_neighbors = pd.DataFrame({
        'cell_id': df_features['cell_id'],
        'x': df_features['x'],
        'y': df_features['y'],
        'z': df_features['z'],
        'nearest_twin_id': [df_features['cell_id'].iloc[i] for i in nearest_idx],
        'morphological_distance': nearest_dists
    })
    
    print(f"Saving morphological twins to {out_neighbors}")
    df_neighbors.to_csv(out_neighbors, index=False)
    
    print("========================================")
    print(f"Total Pipeline Runtime: {time.time() - start_total:.2f} seconds")
    print("========================================")

if __name__ == '__main__':
    main()
