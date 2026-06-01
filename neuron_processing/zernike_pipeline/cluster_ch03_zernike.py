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
    import argparse
    parser = argparse.ArgumentParser(description="Zernike Feature Pipeline: Feature Extraction, Clustering & Napari Visualizer")
    parser.add_argument("--volume", "-v", type=str, default=r'c:\Users\banerjee\Desktop\um1_3d_volume\docker_cell_detection\F0200_multichannel_cmle_ch03.tif',
                        help="Path to the input TIFF volume")
    parser.add_argument("--centroids", "-c", type=str, default=r'c:\Users\banerjee\Desktop\um1_3d_volume\docker_cell_detection\centroids_DAPI_scaled.swc',
                        help="Path to the centroids SWC file")
    parser.add_argument("--n_clusters", "-k", type=int, default=10,
                        help="Number of clusters for K-Means")
    parser.add_argument("--sphere_multiplier", "-s", type=float, default=2.0,
                        help="Size scaling factor for the enclosing bounding sphere")
    parser.add_argument("--crop_size", type=str, default="50,150,150",
                        help="Comma-separated bounding box crop dimensions (Z,Y,X)")
    parser.add_argument("--out_features", type=str, default=None,
                        help="Path to save the output invariants CSV file")
    
    parser.add_argument("--point_size", type=float, default=5.0,
                        help="Point size for Napari visualization markers")
    
    args = parser.parse_args()
    
    print("==================================================")
    print("   Zernike Feature Pipeline: Extraction & Clustering ")
    print("   Created by: Samik Banerjee @ Mitralab @ CSHL  ")
    print("==================================================")
    
    # 1. Setup paths
    base_dir = r'c:\Users\banerjee\Desktop\um1_3d_volume'
    tif_path = args.volume
    swc_path = args.centroids
    optimal_keys_path = os.path.join(base_dir, r'neuron_processing\output\custom_crops\optimal_basis_keys.json')
    
    if args.out_features:
        out_features = args.out_features
    else:
        vol_basename = os.path.splitext(os.path.basename(tif_path))[0]
        out_features = os.path.join(base_dir, f'neuron_processing\\output\\custom_crops\\zernike_features_{vol_basename}.csv')
    
    voxel_spacing = (0.5, 0.1102, 0.1102)
    try:
        Z_dim, Y_dim, X_dim = map(int, args.crop_size.split(','))
    except Exception:
        print("Invalid crop_size format. Using default 50,150,150")
        Z_dim, Y_dim, X_dim = 50, 150, 150
    
    # 2. Compile Filter Bank
    filter_bank = ZernikeFilterBank(
        optimal_keys_path, 
        voxel_spacing, 
        z_dim=Z_dim, 
        y_dim=Y_dim, 
        x_dim=X_dim,
        sphere_multiplier=args.sphere_multiplier
    )
    
    # 3. Load full 4GB image
    print(f"\nLoading volume: {tif_path}")
    vol = tifffile.imread(tif_path)
    max_z, max_y, max_x = vol.shape
    
    # 4. Load Centroids
    print(f"Loading centroids from {swc_path}")
    df_centroids = pd.read_csv(swc_path, sep=' ', comment='#', header=None, 
                               names=['id', 'type', 'x', 'y', 'z', 'r', 'p'])
    
    num_cells = len(df_centroids)
    print(f"Found {num_cells} cells. Extracting features...")
    
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
            
        # Perform 3D histogram equalization to normalize intensities across cells
        from skimage.exposure import equalize_hist
        crop_equalized = equalize_hist(crop).astype(np.float32)
            
        moments, _ = filter_bank.extract(crop_equalized)
        inv = compute_invariants(moments)
        inv['cell_id'] = c_id
        features_list.append(inv)
        
        if (index + 1) % 100 == 0:
            print(f"Processed {index + 1}/{num_cells} cells...")
            
    print(f"Extraction complete! Processed {num_cells} cells in {time.time() - batch_start:.2f}s.")
    
    df_features = pd.DataFrame(features_list)
    df_features.to_csv(out_features, index=False)
    print(f"Features saved to {out_features}")
    
    # 5. K-Means clustering
    k_clusters = args.n_clusters
    print(f"\nPerforming K-Means Clustering (K={k_clusters}) on shell invariants...")
    feature_cols = [c for c in df_features.columns if c.startswith('F_')]
    X = df_features[feature_cols].values
    
    # Normalize features to prevent scale bias
    from sklearn.preprocessing import StandardScaler
    X_scaled = StandardScaler().fit_transform(X)
    
    kmeans = KMeans(n_clusters=k_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X_scaled)
    
    df_centroids['cluster'] = cluster_labels
    coords_phys = np.array(coords_phys)
    
    # Define color list for visualization
    base_colors = [
        'red', 'green', 'blue', 'yellow', 'magenta', 
        'cyan', 'orange', 'pink', 'purple', 'white',
        'lightgreen', 'darkred', 'violet', 'gold', 'teal'
    ]
    colors = [base_colors[i % len(base_colors)] for i in range(k_clusters)]
    
    print("\nCluster assignment breakdown:")
    cluster_coords_dict = {}
    for k in range(k_clusters):
        coords_k = coords_phys[cluster_labels == k]
        cluster_coords_dict[k] = coords_k
        print(f"  Cluster {k}: {len(coords_k)} cells ({colors[k].capitalize()})")
        
    # 6. Napari Visualization
    print("\nLaunching Napari Viewer...")
    viewer = napari.Viewer()
    
    # Display volume
    viewer.add_image(
        vol, 
        name='Volume', 
        scale=voxel_spacing, 
        blending='additive', 
        colormap='gray'
    )
    
    # Dynamically display each cluster as a separate point layer
    for k in range(k_clusters):
        viewer.add_points(
            cluster_coords_dict[k],
            name=f'Cluster {k} ({colors[k].capitalize()})',
            size=args.point_size,
            face_color=colors[k],
            border_color='white',
            blending='translucent'
        )
    
    napari.run()

if __name__ == '__main__':
    main()
