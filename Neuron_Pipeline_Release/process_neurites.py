"""
process_neurites.py (neurite_detection)

Author: Samik Banerjee
Date: June 5, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

High-speed GPU-accelerated Frangi vesselness filter for neurite detection.
"""

import os
import sys
import time
import argparse
import tifffile
import numpy as np
import scipy.ndimage as ndi
from skimage.filters import frangi
from skimage import exposure
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import cupy as cp
    import cupyx.scipy.ndimage as cp_ndi
    HAS_GPU = True
    
    frangi_kernel = cp.ElementwiseKernel(
        'float32 Dzz, float32 Dyy, float32 Dxx, float32 Dzy, float32 Dzx, float32 Dyx, float32 alpha, float32 beta, float32 c_val',
        'float32 vess',
        '''
        float q = (Dzz + Dyy + Dxx) / 3.0f;
        float p2 = (Dzz - q)*(Dzz - q) + (Dyy - q)*(Dyy - q) + (Dxx - q)*(Dxx - q) + 2.0f * (Dzy*Dzy + Dzx*Dzx + Dyx*Dyx);
        float p = sqrt(p2 / 6.0f);
        float p_safe = (p < 1e-9f) ? 1e-9f : p;
        float B0_00 = (Dzz - q) / p_safe;
        float B0_11 = (Dyy - q) / p_safe;
        float B0_22 = (Dxx - q) / p_safe;
        float B0_01 = Dzy / p_safe;
        float B0_02 = Dzx / p_safe;
        float B0_12 = Dyx / p_safe;
        float det_B0 = (B0_00 * (B0_11 * B0_22 - B0_12*B0_12) - B0_01 * (B0_01 * B0_22 - B0_02 * B0_12) + B0_02 * (B0_01 * B0_12 - B0_02 * B0_11));
        float r = det_B0 / 2.0f;
        if (r < -1.0f) r = -1.0f;
        if (r > 1.0f) r = 1.0f;
        float phi = acos(r) / 3.0f;
        float pi = 3.141592653589793f;
        float e1 = 2.0f * cos(phi);
        float e2 = 2.0f * cos(phi + 2.0f * pi / 3.0f);
        float e3 = 2.0f * cos(phi + 4.0f * pi / 3.0f);
        float l1 = q + p * e1;
        float l2 = q + p * e2;
        float l3 = q + p * e3;
        float abs_l1 = abs(l1);
        float abs_l2 = abs(l2);
        float abs_l3 = abs(l3);
        float ls1, ls2, ls3;
        if (abs_l1 <= abs_l2) {
            if (abs_l2 <= abs_l3) { ls1 = l1; ls2 = l2; ls3 = l3; }
            else if (abs_l1 <= abs_l3) { ls1 = l1; ls2 = l3; ls3 = l2; }
            else { ls1 = l3; ls2 = l1; ls3 = l2; }
        } else {
            if (abs_l1 <= abs_l3) { ls1 = l2; ls2 = l1; ls3 = l3; }
            else if (abs_l2 <= abs_l3) { ls1 = l2; ls2 = l3; ls3 = l1; }
            else { ls1 = l3; ls2 = l2; ls3 = l1; }
        }
        float Ra = abs(ls2) / (abs(ls3) + 1e-8f);
        float Rb = abs(ls1) / (sqrt(abs(ls2 * ls3)) + 1e-8f);
        float S = sqrt(ls1*ls1 + ls2*ls2 + ls3*ls3);
        if (ls2 < 0.0f && ls3 < 0.0f) {
            float term_a = 1.0f - exp(-(Ra*Ra) / (2.0f * alpha*alpha));
            float term_b = exp(-(Rb*Rb) / (2.0f * beta*beta));
            float term_c = 1.0f - exp(-(S*S) / (2.0f * c_val*c_val));
            vess = term_a * term_b * term_c;
        } else {
            vess = 0.0f;
        }
        ''',
        'frangi_vesselness'
    )
except ImportError:
    HAS_GPU = False

def cupy_frangi_3d(volume, sigmas, alpha=0.5, beta=0.5, c=None):
    max_vesselness = cp.zeros_like(volume)
    for sigma in sigmas:
        Dzz = cp_ndi.gaussian_filter(volume, sigma=sigma, order=[2, 0, 0])
        Dyy = cp_ndi.gaussian_filter(volume, sigma=sigma, order=[0, 2, 0])
        Dxx = cp_ndi.gaussian_filter(volume, sigma=sigma, order=[0, 0, 2])
        Dzy = cp_ndi.gaussian_filter(volume, sigma=sigma, order=[1, 1, 0])
        Dzx = cp_ndi.gaussian_filter(volume, sigma=sigma, order=[1, 0, 1])
        Dyx = cp_ndi.gaussian_filter(volume, sigma=sigma, order=[0, 1, 1])
        
        if c is None:
            S_est = cp.sqrt(Dzz**2 + Dyy**2 + Dxx**2 + 2.0 * (Dzy**2 + Dzx**2 + Dyx**2))
            c_val = 0.5 * cp.max(S_est)
            if c_val <= 0:
                c_val = 1e-5
            del S_est
        else:
            c_val = c
            
        vess = cp.zeros_like(volume)
        frangi_kernel(Dzz, Dyy, Dxx, Dzy, Dzx, Dyx, float(alpha), float(beta), float(c_val), vess)
        max_vesselness = cp.maximum(max_vesselness, vess)
        del Dzz, Dyy, Dxx, Dzy, Dzx, Dyx, vess
        
    return max_vesselness

GLOBAL_VOL = None

def process_tile_gpu(args):
    tile_coords, sigmas, neurite_params = args
    zs, ze, ys, ye, xs, xe, p_z, p_y, p_x = tile_coords
    print(f"Starting GPU tile: Z[{zs}:{ze}] Y[{ys}:{ye}] X[{xs}:{xe}]")
    depth, height, width = GLOBAL_VOL.shape
    
    z_start_pad = max(0, zs - p_z)
    z_end_pad = min(depth, ze + p_z)
    y_start_pad = max(0, ys - p_y)
    y_end_pad = min(height, ye + p_y)
    x_start_pad = max(0, xs - p_x)
    x_end_pad = min(width, xe + p_x)
    
    crop_data = GLOBAL_VOL[z_start_pad:z_end_pad, y_start_pad:y_end_pad, x_start_pad:x_end_pad]
    
    with cp.cuda.Stream():
        gpu_tile = cp.asarray(crop_data)
        
        chunk_max = gpu_tile.max()
        chunk_min = gpu_tile.min()
        bg_thresh = neurite_params.get('bg_thresh', 0)
        
        if chunk_max < bg_thresh:
            import gc
            gc.collect()
            cp.get_default_memory_pool().free_all_blocks()
            return (zs, ze, ys, ye, xs, xe), np.zeros((ze-zs, ye-ys, xe-xs), dtype=np.uint8)
            
        # Use global normalization to prevent empty tiles from amplifying noise
        global_max = neurite_params.get('global_max', 255.0)
        global_min = neurite_params.get('global_min', 0.0)
        
        gpu_tile_norm = gpu_tile.astype(cp.float32)
        gpu_tile_norm = (gpu_tile_norm - global_min) / (global_max - global_min + 1e-8)
        
        # Fill hollow tubes (membrane stains) to create solid cores for Frangi
        gpu_tile_norm = cp_ndi.grey_closing(gpu_tile_norm, size=(5, 5, 5))
        gpu_tile_norm = gpu_tile_norm.astype(cp.float32)
        
        # CRITICAL FIX for Tiling Artifacts:
        # Frangi inherently auto-normalizes its 'c' parameter (structureness norm) based on the MAX Hessian of the CURRENT TILE.
        # In an empty tile, the max Hessian is pure noise, so the noise gets amplified to 1.0!
        # By forcing a fixed global c=5e-4, we completely eliminate this per-tile noise amplification.
        vesselness = cupy_frangi_3d(gpu_tile_norm, sigmas=sigmas, c=5e-4)
        vesselness_smooth = cp_ndi.gaussian_filter(vesselness, sigma=1.5)
        
        # Mask out very faint pixels to avoid faint neurites and amplified noise
        intensity_mask = gpu_tile > bg_thresh
        vesselness_smooth = vesselness_smooth * intensity_mask
        
        # Pure Absolute Thresholding: Since the input is globally normalized, Frangi outputs are globally comparable.
        # We completely abandon per-tile percentiles because they cause bright tiles to suppress faint neurites
        # and empty tiles to amplify noise. 
        # With c=5e-4, noise yields vesselness ~0.02, and faint vessels yield ~0.4.
        # An absolute threshold of 0.02 aggressively captures faint neurites, while graph pruning cleans the noise!
        absolute_thresh = cp.float32(neurite_params.get('absolute_threshold', 0.02))
            
        binary_neurite = vesselness_smooth > absolute_thresh
        
        # Fast sparse structure (7 elements instead of 125)
        struct_fast_gpu = cp.asarray(ndi.generate_binary_structure(3, 1))
        
        # Removed the massive 5-iteration closing that was fusing noise specks into giant meshes!
        # A single sparse closing is enough to connect 1-pixel gaps.
        binary_neurite = cp_ndi.binary_dilation(binary_neurite, structure=struct_fast_gpu)
        binary_neurite = cp_ndi.binary_erosion(binary_neurite, structure=struct_fast_gpu)
        
        # Fast sparse dilation
        ds = neurite_params.get('dilation_size', 2)
        for _ in range(ds):
            binary_neurite = cp_ndi.binary_dilation(binary_neurite, structure=struct_fast_gpu)
        
        # Fast sparse opening
        binary_neurite = cp_ndi.binary_erosion(binary_neurite, structure=struct_fast_gpu)
        binary_neurite = cp_ndi.binary_dilation(binary_neurite, structure=struct_fast_gpu)
        
        neurite_crop = cp.asnumpy(binary_neurite)
                
        z_keep_start = zs - z_start_pad
        z_keep_end = z_keep_start + (ze - zs)
        y_keep_start = ys - y_start_pad
        y_keep_end = y_keep_start + (ye - ys)
        x_keep_start = xs - x_start_pad
        x_keep_end = x_keep_start + (xe - xs)
        
        neurite_clean = neurite_crop[z_keep_start:z_keep_end, y_keep_start:y_keep_end, x_keep_start:x_keep_end]
        
    # CRITICAL: Force garbage collection in the WORKER THREAD before returning!
    # CuPy memory pools are thread-local, so freeing them in the main thread does NOTHING!
    import gc
    gc.collect()
    cp.get_default_memory_pool().free_all_blocks()
        
    return (zs, ze, ys, ye, xs, xe), neurite_clean

def detect_neurites_volume(volume_path, output_path, workers=4, tile_size=(64, 512, 512), overlap=(10, 20, 20)):
    global GLOBAL_VOL
    t0 = time.time()
    
    if isinstance(volume_path, str):
        print(f"Loading whole volume: {volume_path}")
        GLOBAL_VOL = tifffile.imread(volume_path)
    else:
        print("Using pre-loaded volume from memory.")
        GLOBAL_VOL = volume_path
    depth, height, width = GLOBAL_VOL.shape
    print(f"Volume loaded. Shape: ({depth}, {height}, {width}). Time complexity O(N) memory load: {time.time()-t0:.2f}s")
    
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
                
    neurite_out = np.zeros((depth, height, width), dtype=np.uint8)
    
    print("Calculating global background threshold and normalization stats...")
    global_bg_thresh = np.percentile(GLOBAL_VOL[::8, ::8, ::8], 80)
    global_max = float(GLOBAL_VOL.max())
    global_min = float(GLOBAL_VOL.min())
    print(f"Global background intensity threshold set to: {global_bg_thresh:.1f}")
    
    # We remove sigmas 16 and 20 because they detect thick somas which we already handled!
    # This cuts computation time by 40%!
    sigmas = [4, 8, 12]
    neurite_params = {
        'absolute_threshold': 0.02, 
        'bg_thresh': global_bg_thresh,
        'global_max': global_max,
        'global_min': global_min
    }
    
    print(f"Processing {len(tile_tasks)} tiles on GPU with sigmas {sigmas}...")
    t1 = time.time()
    
    if HAS_GPU:
        processed_count = 0
        task_args = [(task, sigmas, neurite_params) for task in tile_tasks]
        
        # Reducing to 1 worker to prevent GPU VRAM exhaustion and PCIe paging!
        with ThreadPoolExecutor(max_workers=1) as executor:
            futures = {executor.submit(process_tile_gpu, arg): arg for arg in task_args}
            for future in as_completed(futures):
                try:
                    coords, neurite_clean = future.result()
                    zs, ze, ys, ye, xs, xe = coords
                    neurite_out[zs:ze, ys:ye, xs:xe] = neurite_clean.astype(np.uint8) * 255
                    
                    processed_count += 1
                    # Print EVERY tile so we can see live progress in unbuffered mode!
                    print(f"Processed {processed_count}/{len(tile_tasks)} tiles...")
                except Exception as exc:
                    print(f"GPU Tile generated an exception: {exc}")
    else:
        print("ERROR: GPU/CuPy not found. Processing aborting.")
        sys.exit(1)
        
    t2 = time.time()
    print(f"Filtering Time Complexity: {t2 - t1:.2f}s")
    
    if output_path is not None:
        print(f"Saving binary mask to {output_path}")
        tifffile.imwrite(output_path, neurite_out)
    print(f"Total Pipeline Time: {time.time() - t0:.2f}s")
    
    return neurite_out

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help="Input TIFF")
    parser.add_argument('--output', required=True, help="Output binary TIFF")
    parser.add_argument('--workers', type=int, default=1, help="Number of GPU workers")
    args = parser.parse_args()
    detect_neurites_volume(args.input, args.output, workers=args.workers)
