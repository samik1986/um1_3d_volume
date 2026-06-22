import time
import numpy as np
import tifffile
import scipy.ndimage as ndi
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

import sys
import os

try:
    import cupy as cp
    import cupy_backends
    os.environ["CUDA_PATH"] = os.path.dirname(cupy_backends.__file__)
    import cupyx.scipy.ndimage as cp_ndi
    HAS_GPU = True
except ImportError:
    HAS_GPU = False
except ImportError:
    HAS_GPU = False

GLOBAL_VOL = None
gpu_semaphore = threading.Semaphore(1)

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
    
    sigma_smooth = params.get('sigma_smooth', 5)
    sigma_bg = params.get('sigma_bg', 20)
    
    with gpu_semaphore:
        with cp.cuda.Stream():
            gpu_tile = cp.asarray(crop_data, dtype=cp.float32)
            v_smooth = cp_ndi.gaussian_filter(gpu_tile, sigma=sigma_smooth)
            v_bg = cp_ndi.gaussian_filter(gpu_tile, sigma=sigma_bg)
            
            v_sub = v_smooth - v_bg
            v_sub = cp.maximum(v_sub, 0)
            
            thresh = cp.percentile(v_sub, params.get('threshold_percentile', 99.5))
            binary_soma = v_sub > thresh
            
            struct = cp.ones((3, 3, 3), dtype=bool)
            for _ in range(4):
                binary_soma = cp_ndi.binary_erosion(binary_soma, structure=struct)
            for _ in range(4):
                binary_soma = cp_ndi.binary_dilation(binary_soma, structure=struct)
            
            soma_crop = cp.asnumpy(binary_soma)
                    
            z_keep_start = zs - z_start_pad
        z_keep_end = z_keep_start + (ze - zs)
        y_keep_start = ys - y_start_pad
        y_keep_end = y_keep_start + (ye - ys)
        x_keep_start = xs - x_start_pad
        x_keep_end = x_keep_start + (xe - xs)
        
        soma_clean = soma_crop[z_keep_start:z_keep_end, y_keep_start:y_keep_end, x_keep_start:x_keep_end]
        cp.get_default_memory_pool().free_all_blocks()
        
    return (zs, ze, ys, ye, xs, xe), soma_clean

def detect_cells_488(image_path, workers=4, tile_size=(64, 512, 512), overlap=(10, 20, 20)):
    global GLOBAL_VOL
    print(f"\n--- Detecting Somas on 488 Channel ---")
    t0 = time.time()
    
    GLOBAL_VOL = tifffile.imread(image_path)
    
    # Load and apply pipeline parameters
    param_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pipeline_parameters.json")
    if os.path.exists(param_path):
        import json
        with open(param_path, 'r') as f:
            params = json.load(f)
            gamma = params.get('gamma', 1.0)
            c_min, c_max = params.get('contrast_limits', [0, 65535])
            print(f"Applying interactive parameters: Gamma={gamma}, Contrast=[{c_min}, {c_max}]")
            np.clip(GLOBAL_VOL, np.uint16(c_min), np.uint16(c_max), out=GLOBAL_VOL)
            GLOBAL_VOL = GLOBAL_VOL.astype(np.float32, copy=False)
            GLOBAL_VOL -= c_min
            GLOBAL_VOL /= np.float32(c_max - c_min + 1e-8)
            if gamma != 1.0:
                GLOBAL_VOL = np.power(GLOBAL_VOL, gamma, out=GLOBAL_VOL)
            GLOBAL_VOL *= 65535.0
            GLOBAL_VOL = GLOBAL_VOL.astype(np.uint16)

    depth, height, width = GLOBAL_VOL.shape
    
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
    soma_params = {'sigma_smooth': 5, 'sigma_bg': 20, 'threshold_percentile': 98.5}
    
    if HAS_GPU:
        print(f"Processing {len(tile_tasks)} tiles for somas on GPU...")
        processed_count = 0
        task_args = [(task, soma_params) for task in tile_tasks]
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(process_tile_soma_gpu, arg): arg for arg in task_args}
            for future in as_completed(futures):
                coords, soma_clean = future.result()
                zs, ze, ys, ye, xs, xe = coords
                binary_out[zs:ze, ys:ye, xs:xe] = soma_clean
                processed_count += 1
                if processed_count % 20 == 0:
                    cp.get_default_memory_pool().free_all_blocks()
    else:
        print("ERROR: GPU/CuPy not found.")
        return np.empty((0,3)), None
        
    print("Transferring volume to GPU for Bouton Filtration & Connected Components...")
    gpu_binary = cp.asarray(binary_out)
    labels_gpu, num_features = cp_ndi.label(gpu_binary)
    
    print(f"Found {num_features} initial structures. Filtering synaptic boutons (< 3000 voxels)...")
    voxel_counts = cp.bincount(labels_gpu.ravel())
    keep_mask = voxel_counts >= 3000
    keep_mask[0] = False
    
    filtered_gpu_binary = keep_mask[labels_gpu]
    labels_gpu, num_features = cp_ndi.label(filtered_gpu_binary)
    
    print(f"Surviving massive Somas: {num_features}. Extracting centroids on CPU...")
    binary_out = cp.asnumpy(filtered_gpu_binary)
    labels_out = cp.asnumpy(labels_gpu)
    cp.get_default_memory_pool().free_all_blocks()
    
    if num_features > 0:
        slices = ndi.find_objects(labels_out)
        centroids_list = []
        for i, slc in enumerate(slices):
            if slc is not None:
                crop_binary = binary_out[slc]
                crop_labels = labels_out[slc]
                local_com = ndi.center_of_mass(crop_binary, crop_labels, i + 1)
                global_z = slc[0].start + local_com[0]
                global_y = slc[1].start + local_com[1]
                global_x = slc[2].start + local_com[2]
                centroids_list.append([global_z, global_y, global_x])
        centroids = np.array(centroids_list)
    else:
        centroids = np.empty((0,3))
        
    print(f"Soma detection finished in {time.time()-t0:.2f}s")
    
    del GLOBAL_VOL
    GLOBAL_VOL = None
    import gc
    gc.collect()
    
    return centroids, binary_out
