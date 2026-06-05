"""
detect_somas.py (neurite_detection)

Author: Samik Banerjee
Date: June 5, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

GPU-accelerated tiled soma detection using CuPy.
Extracts 3D soma labels from the volumetric channel.
"""

import sys
import time
import argparse
import tifffile
import numpy as np
import scipy.ndimage as ndi
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import cupy as cp
    import cupyx.scipy.ndimage as cp_ndi
    HAS_GPU = True
except ImportError:
    HAS_GPU = False

GLOBAL_VOL = None

def process_tile_soma_gpu(args):
    tile_coords, params = args
    zs, ze, ys, ye, xs, xe, p_z, p_y, p_x = tile_coords
    depth, height, width = GLOBAL_VOL.shape
    
    z_start_pad = max(0, zs - p_z)
    z_end_pad = min(depth, ze + p_z)
    y_start_pad = max(0, ys - p_y)
    y_end_pad = min(height, ye + p_y)
    x_start_pad = max(0, xs - p_x)
    x_end_pad = min(width, xe + p_x)
    
    crop_data = GLOBAL_VOL[z_start_pad:z_end_pad, y_start_pad:y_end_pad, x_start_pad:x_end_pad]
    
    sigma_smooth = params.get('sigma_smooth', 15)
    sigma_bg = params.get('sigma_bg', 40)
    
    with cp.cuda.Stream():
        gpu_tile = cp.asarray(crop_data, dtype=cp.float32)
        
        # High frequency smoothing
        v_smooth = cp_ndi.gaussian_filter(gpu_tile, sigma=sigma_smooth)
        # Background subtraction
        v_bg = cp_ndi.gaussian_filter(gpu_tile, sigma=sigma_bg)
        
        v_sub = v_smooth - v_bg
        v_sub = cp.maximum(v_sub, 0) # ReLU
        
        thresh = cp.percentile(v_sub, params.get('threshold_percentile', 98))
        binary_soma = v_sub > thresh
        
        # Morphological cleanup
        struct_open = cp.ones((3, 3, 3), dtype=bool)
        binary_soma = cp_ndi.binary_opening(binary_soma, structure=struct_open)
        
        soma_crop = cp.asnumpy(binary_soma)
                
        z_keep_start = zs - z_start_pad
        z_keep_end = z_keep_start + (ze - zs)
        y_keep_start = ys - y_start_pad
        y_keep_end = y_keep_start + (ye - ys)
        x_keep_start = xs - x_start_pad
        x_keep_end = x_keep_start + (xe - xs)
        
        soma_clean = soma_crop[z_keep_start:z_keep_end, y_keep_start:y_keep_end, x_keep_start:x_keep_end]
        
    return (zs, ze, ys, ye, xs, xe), soma_clean

def detect_somas(volume_path, output_path, workers=4, tile_size=(64, 512, 512), overlap=(10, 20, 20)):
    global GLOBAL_VOL
    t0 = time.time()
    
    print(f"Loading whole volume for somas: {volume_path}")
    GLOBAL_VOL = tifffile.imread(volume_path)
    depth, height, width = GLOBAL_VOL.shape
    print(f"Volume loaded. Time complexity O(N): {time.time()-t0:.2f}s")
    
    tile_depth, tile_height, tile_width = tile_size
    pad_z, pad_y, pad_x = overlap
    
    z_coords = [(z, min(depth, z + tile_depth)) for z in range(0, depth, tile_depth)]
    y_coords = [(y, min(height, y + tile_height)) for y in range(0, height, tile_height)]
    x_coords = [(x, min(width, x + tile_width)) for x in range(0, width, tile_width)]
    
    tile_tasks = []
    for zs, ze in z_coords:
        for ys, ye in y_coords:
            for xs, xe in x_coords:
                tile_tasks.append((zs, ze, ys, ye, xs, xe, pad_z, pad_y, pad_x))
                
    binary_out = np.zeros((depth, height, width), dtype=bool)
    soma_params = {'sigma_smooth': 5, 'sigma_bg': 20, 'threshold_percentile': 99.5} # Adjusted for speed and specificity
    
    print(f"Processing {len(tile_tasks)} tiles on GPU...")
    t1 = time.time()
    
    if HAS_GPU:
        processed_count = 0
        task_args = [(task, soma_params) for task in tile_tasks]
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(process_tile_soma_gpu, arg): arg for arg in task_args}
            for future in as_completed(futures):
                coords, soma_clean = future.result()
                zs, ze, ys, ye, xs, xe = coords
                binary_out[zs:ze, ys:ye, xs:xe] = soma_clean
                
                processed_count += 1
                if processed_count % 10 == 0 or processed_count == len(tile_tasks):
                    print(f"Processed {processed_count}/{len(tile_tasks)} tiles")
                    
                # Periodically free memory pool in the main thread to prevent fragmentation
                if processed_count % 20 == 0:
                    cp.get_default_memory_pool().free_all_blocks()
    else:
        print("ERROR: GPU/CuPy not found.")
        sys.exit(1)
        
    print(f"Filtering complete in {time.time() - t1:.2f}s")
    
    print("Running global connected components labeling on CPU...")
    t2 = time.time()
    labels_out, num_features = ndi.label(binary_out)
    print(f"Found {num_features} somas in {time.time() - t2:.2f}s")
    
    print(f"Saving soma labels mask to {output_path}")
    tifffile.imwrite(output_path, labels_out.astype(np.uint16))
    
    print(f"Total Soma Pipeline Time: {time.time() - t0:.2f}s")
    return output_path

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help="Input TIFF")
    parser.add_argument('--output', required=True, help="Output labels TIFF")
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()
    detect_somas(args.input, args.output, args.workers)
