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
        gpu_tile_norm = gpu_tile.astype(cp.float32)
        gpu_tile_norm = (gpu_tile_norm - gpu_tile_norm.min()) / (gpu_tile_norm.max() - gpu_tile_norm.min() + 1e-8)
        
        vesselness = cupy_frangi_3d(gpu_tile_norm, sigmas=sigmas)
        vesselness_smooth = cp_ndi.gaussian_filter(vesselness, sigma=1)
        
        # Hysteresis Thresholding
        thresh_high = cp.percentile(vesselness_smooth, neurite_params.get('threshold_percentile', 98))
        thresh_low = cp.percentile(vesselness_smooth, neurite_params.get('threshold_low_percentile', 85))
        
        binary_high = vesselness_smooth > thresh_high
        binary_low = vesselness_smooth > thresh_low
        
        struct_propagate = cp.ones((3, 3, 3), dtype=bool)
        binary_neurite = binary_high.copy()
        
        for _ in range(15): # 15 iterations of morphological reconstruction
            dilated = cp_ndi.binary_dilation(binary_neurite, structure=struct_propagate)
            new_binary = cp.logical_and(dilated, binary_low)
            if cp.array_equal(new_binary, binary_neurite):
                break
            binary_neurite = new_binary
        
        struct_closing = cp.ones((5, 5, 5), dtype=bool)
        ds = neurite_params.get('dilation_size', 2)
        struct_dilation = cp.ones((ds, ds, ds), dtype=bool)
        binary_neurite = cp_ndi.binary_closing(binary_neurite, structure=struct_closing)
        binary_neurite = cp_ndi.binary_dilation(binary_neurite, structure=struct_dilation)
        
        struct_opening = cp.ones((3, 3, 3), dtype=bool)
        binary_neurite = cp_ndi.binary_opening(binary_neurite, structure=struct_opening)
        
        neurite_crop = cp.asnumpy(binary_neurite)
                
        z_keep_start = zs - z_start_pad
        z_keep_end = z_keep_start + (ze - zs)
        y_keep_start = ys - y_start_pad
        y_keep_end = y_keep_start + (ye - ys)
        x_keep_start = xs - x_start_pad
        x_keep_end = x_keep_start + (xe - xs)
        
        neurite_clean = neurite_crop[z_keep_start:z_keep_end, y_keep_start:y_keep_end, x_keep_start:x_keep_end]
        cp.get_default_memory_pool().free_all_blocks()
        
    return (zs, ze, ys, ye, xs, xe), neurite_clean

def detect_neurites_volume(volume_path, output_path, workers=4, tile_size=(64, 512, 512), overlap=(10, 20, 20)):
    global GLOBAL_VOL
    t0 = time.time()
    
    print(f"Loading whole volume: {volume_path}")
    GLOBAL_VOL = tifffile.imread(volume_path)
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
    
    neurite_params = {'dilation_size': 2, 'threshold_percentile': 98}
    sigmas = [4, 8, 12]
    
    print(f"Processing {len(tile_tasks)} tiles. Estimated Time Complexity: O(N * T) where N is voxels, T is scales. GPU workers: {workers}")
    t1 = time.time()
    
    if HAS_GPU:
        processed_count = 0
        task_args = [(task, sigmas, neurite_params) for task in tile_tasks]
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(process_tile_gpu, arg): arg for arg in task_args}
            for future in as_completed(futures):
                try:
                    coords, neurite_clean = future.result()
                    zs, ze, ys, ye, xs, xe = coords
                    neurite_out[zs:ze, ys:ye, xs:xe] = neurite_clean.astype(np.uint8) * 255
                    
                    processed_count += 1
                    if processed_count % 5 == 0 or processed_count == len(tile_tasks):
                        print(f"Processed {processed_count}/{len(tile_tasks)} tiles ({processed_count/len(tile_tasks)*100:.1f}%)")
                except Exception as exc:
                    print(f"GPU Tile generated an exception: {exc}")
    else:
        print("ERROR: GPU/CuPy not found. Processing aborting.")
        sys.exit(1)
        
    t2 = time.time()
    print(f"Filtering Time Complexity: {t2 - t1:.2f}s")
    
    print(f"Saving binary mask to {output_path}")
    tifffile.imwrite(output_path, neurite_out)
    print(f"Total Pipeline Time: {time.time() - t0:.2f}s")
    
    return output_path

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help="Input TIFF")
    parser.add_argument('--output', required=True, help="Output binary TIFF")
    args = parser.parse_args()
    detect_neurites_volume(args.input, args.output)
