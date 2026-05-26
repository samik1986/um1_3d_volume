import os
import time
import math
import numpy as np
import cupy as cp
import cupyx.scipy.signal
import tifffile
from scipy.ndimage import maximum_filter
from scipy.spatial.distance import cdist

def generate_z00_kernel(z_dim, y_dim, x_dim, voxel_spacing):
    """
    Generates the physical Z_00^0 kernel (spherical mass detector).
    It is exactly 1.0 inside the physical unit sphere, and 0.0 outside.
    """
    sz, sy, sx = voxel_spacing
    
    z = cp.arange(z_dim, dtype=cp.float32)
    y = cp.arange(y_dim, dtype=cp.float32)
    x = cp.arange(x_dim, dtype=cp.float32)
    
    z -= z_dim / 2.0
    y -= y_dim / 2.0
    x -= x_dim / 2.0
    
    Z, Y, X = cp.meshgrid(z, y, x, indexing='ij')
    
    # Scale to physical units
    Z *= sz
    Y *= sy
    X *= sx
    
    # Radial distance squared
    R2 = X**2 + Y**2 + Z**2
    
    # Physical sphere radius
    R_max = max((x_dim/2)*sx, (y_dim/2)*sy, (z_dim/2)*sz)
    
    # Normalize radius to [0, 1]
    R_norm = cp.sqrt(R2) / R_max
    
    # Z_00^0 is a constant sphere
    kernel = cp.zeros_like(R_norm, dtype=cp.float32)
    kernel[R_norm <= 1.0] = 1.0
    
    # Normalize kernel to sum to 1 to preserve intensity scale
    kernel /= cp.sum(kernel)
    
    return kernel

def main():
    print("========================================")
    print("   Zernike 3D Blob Detection (F00)      ")
    print("========================================")
    start_time = time.time()
    
    base_dir = r'c:\Users\banerjee\Desktop\um1_3d_volume'
    tif_path = os.path.join(base_dir, r'docker_cell_detection\F0200_multichannel_cmle_ch04.tif')
    out_swc_path = os.path.join(base_dir, r'neuron_processing\output\custom_crops\zernike_detected_centroids.swc')
    
    voxel_spacing = (0.5, 0.1102, 0.1102)
    Z_dim, Y_dim, X_dim = 50, 150, 150
    
    # 1. Generate Kernel
    print("Generating Zernike Z_00^0 kernel on GPU...")
    kernel_gpu = generate_z00_kernel(Z_dim, Y_dim, X_dim, voxel_spacing)
    
    # 2. Load Volume
    print(f"\nLoading full 4GB volume: {tif_path}")
    vol = tifffile.imread(tif_path)
    max_z, max_y, max_x = vol.shape
    print(f"Volume shape: {vol.shape}")
    
    # 3. Process in Chunks
    stride_y, stride_x = 500, 500
    overlap_y, overlap_x = Y_dim, X_dim
    chunk_y = stride_y + overlap_y
    chunk_x = stride_x + overlap_x
    
    F00_map = np.zeros_like(vol, dtype=np.float32)
    
    y_starts = list(range(0, max_y, stride_y))
    x_starts = list(range(0, max_x, stride_x))
    
    total_chunks = len(y_starts) * len(x_starts)
    print(f"\nStarting 3D FFT Convolution across {total_chunks} chunks...")
    
    chunk_idx = 0
    for ys in y_starts:
        for xs in x_starts:
            chunk_idx += 1
            ye = min(max_y, ys + chunk_y)
            xe = min(max_x, xs + chunk_x)
            
            # Extract chunk
            chunk_cpu = vol[:, ys:ye, xs:xe].astype(np.float32)
            chunk_gpu = cp.asarray(chunk_cpu)
            
            # 3D FFT Convolution
            resp_gpu = cupyx.scipy.signal.fftconvolve(chunk_gpu, kernel_gpu, mode='same')
            
            # Transfer back to CPU
            resp_cpu = cp.asnumpy(resp_gpu)
            
            # Place in global map (handling overlap logic)
            # We only keep the valid 'stride' region, trimming the overlap.
            
            trim_y_start = overlap_y // 2 if ys > 0 else 0
            trim_y_end = overlap_y // 2 if ye < max_y else 0
            
            trim_x_start = overlap_x // 2 if xs > 0 else 0
            trim_x_end = overlap_x // 2 if xe < max_x else 0
            
            out_ys = ys + trim_y_start
            out_ye = ye - trim_y_end
            
            out_xs = xs + trim_x_start
            out_xe = xe - trim_x_end
            
            in_ys = trim_y_start
            in_ye = resp_cpu.shape[1] - trim_y_end
            
            in_xs = trim_x_start
            in_xe = resp_cpu.shape[2] - trim_x_end
            
            F00_map[:, out_ys:out_ye, out_xs:out_xe] = resp_cpu[:, in_ys:in_ye, in_xs:in_xe]
            
            if chunk_idx % 10 == 0:
                print(f"Processed chunk {chunk_idx}/{total_chunks}...")
                
    print("\nConvolution complete. Finding local maxima...")
    # 4. Local Maxima Detection
    # Using a 3D maximum filter to find peaks
    threshold = 1000.0  # Adjust based on intensity distribution (F00 map)
    # We will use the 95th percentile as a safe threshold
    thresh_val = np.percentile(F00_map[::5, ::10, ::10], 99.0)
    print(f"Applying intensity threshold: {thresh_val:.2f}")
    
    # Apply max filter of cell size (Z=10, Y=30, X=30) to prevent multiple hits on same cell
    neighborhood = maximum_filter(F00_map, size=(10, 30, 30))
    local_maxima = (F00_map == neighborhood) & (F00_map > thresh_val)
    
    # Get coordinates of peaks
    peak_coords = np.argwhere(local_maxima)
    print(f"Found {len(peak_coords)} cells!")
    
    # 5. Save to SWC
    print(f"Saving to {out_swc_path}")
    with open(out_swc_path, 'w') as f:
        f.write("# Zernike F00 Blob Detected Centroids\n")
        f.write("# id type x y z radius parent\n")
        for i, coord in enumerate(peak_coords):
            z, y, x = coord
            f.write(f"{i+1} 2 {x:.6f} {y:.6f} {z:.6f} 1.0 -1\n")
            
    print("========================================")
    print(f"Total Detection Runtime: {time.time() - start_time:.2f} seconds")
    print("========================================")

if __name__ == '__main__':
    main()
