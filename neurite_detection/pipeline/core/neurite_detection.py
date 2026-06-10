import time
import numpy as np
import tifffile
from skimage.filters import threshold_otsu
import skimage.morphology as morph
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

def eigh_3x3_analytical(dxx, dyy, dzz, dxy, dxz, dyz):
    """Analytically solves the roots of a 3x3 symmetric matrix characteristic polynomial using Cardano's method"""
    p1 = dxx + dyy + dzz
    p2 = dxx*dyy + dxx*dzz + dyy*dzz - dxy**2 - dxz**2 - dyz**2
    p3 = dxx*dyy*dzz + 2*dxy*dxz*dyz - dxx*dyz**2 - dyy*dxz**2 - dzz*dxy**2
    
    a = p1 / 3.0
    p = p2 - p1 * a
    q = p1 * p2 / 3.0 - p3 - 2.0 * (a**3)
    
    p_div_3 = p / 3.0
    rho = cp.sqrt(cp.maximum(-p_div_3**3, 0))
    
    theta = cp.arccos(cp.clip(-q / (2.0 * rho + 1e-15), -1.0, 1.0))
    
    sqrt_p = cp.sqrt(cp.maximum(-p_div_3, 0))
    r1 = 2.0 * sqrt_p * cp.cos(theta / 3.0)
    r2 = 2.0 * sqrt_p * cp.cos((theta + 2.0 * cp.pi) / 3.0)
    r3 = 2.0 * sqrt_p * cp.cos((theta + 4.0 * cp.pi) / 3.0)
    
    L1_raw = r1 + a
    L2_raw = r2 + a
    L3_raw = r3 + a
    
    L_stack = cp.stack([L1_raw, L2_raw, L3_raw], axis=-1)
    abs_eig = cp.abs(L_stack)
    sort_indices = cp.argsort(abs_eig, axis=-1)
    L_sorted = cp.take_along_axis(L_stack, sort_indices, axis=-1)
    
    return L_sorted[..., 0], L_sorted[..., 1], L_sorted[..., 2]

def process_tile_frangi_gpu(args):
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
    
    sigmas = params.get('sigmas', [1.0])
    alpha = params.get('alpha', 0.5)
    beta = params.get('beta', 0.5)
    frangi_thresh = params.get('frangi_thresh', 0.05)
    
    with gpu_semaphore:
        with cp.cuda.Stream():
            gpu_tile = cp.asarray(crop_data, dtype=cp.float32)
            max_vesselness = cp.zeros(gpu_tile.shape, dtype=cp.float32)
            
            for sigma in sigmas:
                img_smooth = cp_ndi.gaussian_filter(gpu_tile, sigma)
                
                grad_z = cp.gradient(img_smooth, axis=0)
                grad_y = cp.gradient(img_smooth, axis=1)
                grad_x = cp.gradient(img_smooth, axis=2)
                
                dzz = cp.gradient(grad_z, axis=0) * (sigma ** 2)
                dyy = cp.gradient(grad_y, axis=1) * (sigma ** 2)
                dxx = cp.gradient(grad_x, axis=2) * (sigma ** 2)
                dyz = cp.gradient(grad_y, axis=0) * (sigma ** 2)
                dxz = cp.gradient(grad_x, axis=0) * (sigma ** 2)
                dxy = cp.gradient(grad_x, axis=1) * (sigma ** 2)
                
                del grad_z, grad_y, grad_x, img_smooth
                
                L1, L2, L3 = eigh_3x3_analytical(dxx, dyy, dzz, dxy, dxz, dyz)
                del dxx, dyy, dzz, dxy, dxz, dyz
                
                L2_sq = L2 ** 2
                L3_sq = L3 ** 2
                
                Ra = cp.abs(L2) / (cp.abs(L3) + 1e-10)
                Rb = cp.abs(L1) / cp.sqrt(cp.abs(L2 * L3) + 1e-10)
                S_sq = L1**2 + L2_sq + L3_sq
                del L1, L2_sq, L3_sq
                
                c = cp.max(S_sq) ** 0.5 * 0.5
                if c == 0:
                    c = 1.0
                    
                term1 = 1 - cp.exp(-(Ra**2) / (2 * alpha**2))
                term2 = cp.exp(-(Rb**2) / (2 * beta**2))
                term3 = 1 - cp.exp(-S_sq / (2 * c**2))
                
                del Ra, Rb, S_sq
                
                vesselness = term1 * term2 * term3
                vesselness[L2 > 0] = 0
                vesselness[L3 > 0] = 0
                vesselness[cp.isnan(vesselness)] = 0
                del term1, term2, term3, L2, L3
                
                max_vesselness = cp.maximum(max_vesselness, vesselness)
                del vesselness
                
            del gpu_tile
            vesselness = max_vesselness
            del max_vesselness
            
            high_mask = vesselness > frangi_thresh
            low_mask = vesselness > params.get('low_thresh', 0.005)
            del vesselness
            
            # GPU Hysteresis Thresholding
            labels_low, num_low = cp_ndi.label(low_mask)
            intersecting_labels = cp.unique(labels_low[high_mask])
            valid_labels = intersecting_labels[intersecting_labels > 0]
            binary_neurite = cp.isin(labels_low, valid_labels)
            del labels_low, high_mask, low_mask, valid_labels, intersecting_labels
            
            struct = cp.ones((3, 3, 3), dtype=bool)
            binary_neurite = cp_ndi.binary_closing(binary_neurite, structure=struct)
            
            neurite_crop = cp.asnumpy(binary_neurite)
            del binary_neurite
                    
            z_keep_start = zs - z_start_pad
        z_keep_end = z_keep_start + (ze - zs)
        y_keep_start = ys - y_start_pad
        y_keep_end = y_keep_start + (ye - ys)
        x_keep_start = xs - x_start_pad
        x_keep_end = x_keep_start + (xe - xs)
        
        neurite_clean = neurite_crop[z_keep_start:z_keep_end, y_keep_start:y_keep_end, x_keep_start:x_keep_end]
        cp.get_default_memory_pool().free_all_blocks()
        
    return (zs, ze, ys, ye, xs, xe), neurite_clean

def detect_neurites(image_path, custom_thresh=None, soma_masks=None, use_gpu=True, workers=4, tile_size=(64, 512, 512), overlap=(10, 20, 20)):
    global GLOBAL_VOL
    print(f"\n--- Detecting Neurites: 488 Channel ---")
    t0 = time.time()
    
    GLOBAL_VOL = tifffile.imread(image_path)
    depth, height, width = GLOBAL_VOL.shape
    print(f"Loaded 488 volume: {GLOBAL_VOL.shape} in {time.time()-t0:.2f}s")
    

    
    t1 = time.time()
    
    if use_gpu and HAS_GPU:
        print("Using GPU-accelerated Analytical Frangi Vesselness Filter...")
        
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
        
        frangi_thresh = custom_thresh if custom_thresh is not None else 0.05
        low_thresh = frangi_thresh * 0.20  # dynamically scale the low threshold
        print(f"Adaptive Frangi sensitivity set to: {frangi_thresh} (Seeds) and {low_thresh:.5f} (Faint Path Connections)")
        
        frangi_params = {'sigmas': [1.0, 2.0, 4.0, 6.0, 8.0], 'alpha': 0.5, 'beta': 0.5, 'frangi_thresh': frangi_thresh, 'low_thresh': low_thresh}
        task_args = [(task, frangi_params) for task in tile_tasks]
        
        processed_count = 0
        print(f"Processing {len(tile_tasks)} tiles for neurite manifolds on GPU...")
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(process_tile_frangi_gpu, arg): arg for arg in task_args}
            for future in as_completed(futures):
                coords, neurite_clean = future.result()
                zs, ze, ys, ye, xs, xe = coords
                binary_out[zs:ze, ys:ye, xs:xe] = neurite_clean
                processed_count += 1
                if processed_count % 10 == 0 or processed_count == len(tile_tasks):
                    print(f"Processed {processed_count}/{len(tile_tasks)} tiles")
                if processed_count % 20 == 0:
                    cp.get_default_memory_pool().free_all_blocks()
                    
        binary_cpu = binary_out
    else:
        print("Falling back to CPU global thresholding...")
        if custom_thresh is not None:
            thresh = custom_thresh
        else:
            base_otsu = threshold_otsu(GLOBAL_VOL)
            thresh = base_otsu * 0.7
        binary_cpu = GLOBAL_VOL > thresh
    if soma_masks is not None:
        print(f"Applying soma subtraction on GPU...")
        for s_mask in soma_masks:
            if s_mask is not None:
                gpu_smask = cp.asarray(s_mask > 0)
                # Dilate to create a +-10% buffer zone around the cell membrane
                struct = cp.ones((3,3,3), dtype=bool)
                for _ in range(3):
                    gpu_smask = cp_ndi.binary_dilation(gpu_smask, structure=struct, iterations=1)
                
                gpu_binary = cp.asarray(binary_cpu)
                gpu_binary = gpu_binary & ~gpu_smask
                binary_cpu = cp.asnumpy(gpu_binary)
                del gpu_smask, gpu_binary
                cp.get_default_memory_pool().free_all_blocks()


    print(f"Topological GPU masking complete in {time.time()-t1:.2f}s")
    
    print(f"Applying topological constraints (removing small noise fragments) on GPU...")
    gpu_binary = cp.asarray(binary_cpu)
    labels_gpu, num_features = cp_ndi.label(gpu_binary)
    voxel_counts = cp.bincount(labels_gpu.ravel())
    keep_mask = voxel_counts >= 2000
    keep_mask[0] = False
    filtered_gpu_binary = keep_mask[labels_gpu]
    binary_cpu = cp.asnumpy(filtered_gpu_binary)
    del labels_gpu, voxel_counts, keep_mask, filtered_gpu_binary, gpu_binary
    cp.get_default_memory_pool().free_all_blocks()
    
    print(f"Skeletonizing volume with skimage.morphology (CPU multi-threaded)...")
    t2 = time.time()
    
    # Chunked parallel skeletonization
    tile_z, tile_y, tile_x = 64, 512, 512
    pad = 16
    z_coords = [(z, min(depth, z + tile_z)) for z in range(0, depth, tile_z)]
    y_coords = [(y, min(height, y + tile_y)) for y in range(0, height, tile_y)]
    x_coords = [(x, min(width, x + tile_x)) for x in range(0, width, tile_x)]
    
    binary_skel = np.zeros_like(binary_cpu)
    
    def skel_chunk(coords):
        zs, ze, ys, ye, xs, xe = coords
        pz1, pz2 = max(0, zs-pad), min(depth, ze+pad)
        py1, py2 = max(0, ys-pad), min(height, ye+pad)
        px1, px2 = max(0, xs-pad), min(width, xe+pad)
        
        crop = binary_cpu[pz1:pz2, py1:py2, px1:px2]
        skel = morph.skeletonize(crop)
        
        # Crop back to original bounds
        kz1, kz2 = zs - pz1, (ze - zs) + (zs - pz1)
        ky1, ky2 = ys - py1, (ye - ys) + (ys - py1)
        kx1, kx2 = xs - px1, (xe - xs) + (xs - px1)
        
        return coords, skel[kz1:kz2, ky1:ky2, kx1:kx2]
        
    skel_tasks = []
    for zs, ze in z_coords:
        for ys, ye in y_coords:
            for xs, xe in x_coords:
                skel_tasks.append((zs, ze, ys, ye, xs, xe))
                
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(skel_chunk, t): t for t in skel_tasks}
        for future in as_completed(futures):
            coords, skel = future.result()
            zs, ze, ys, ye, xs, xe = coords
            binary_skel[zs:ze, ys:ye, xs:xe] = skel
            
    print(f"Extracted 3D morphological skeleton in {time.time()-t2:.2f}s")
    
    GLOBAL_VOL = None
    return binary_cpu, binary_skel
