import os
import json
import time
import numpy as np
import cupy as cp
import tifffile
import napari
from zernike_basis_gpu import zernike_3d_basis_physical_gpu

def main():
    target = 'crop_001_ch04'
    base_dir = r'c:\Users\banerjee\Desktop\um1_3d_volume\neuron_processing\output\custom_crops'
    tif_path = os.path.join(base_dir, f'{target}.tif')
    json_path = os.path.join(base_dir, f'{target}_intensity_zernike_gpu_n20.json')
    
    # 1. Load data
    print(f"Loading {tif_path}...")
    orig_vol = tifffile.imread(tif_path).astype(np.float64)
    
    print(f"Loading {json_path}...")
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    voxel_spacing = data['metadata']['voxel_spacing_um']
    raw_moments = data['raw_moments']
    n_max = data['metadata']['n_max']
    
    # 2. Setup GPU grids
    print("Building coordinate grids on GPU...")
    z_dim, y_dim, x_dim = orig_vol.shape
    dz, dy, dx = voxel_spacing
    
    z_idx, y_idx, x_idx = cp.indices((z_dim, y_dim, x_dim))
    
    z_phys = z_idx.flatten() * dz
    y_phys = y_idx.flatten() * dy
    x_phys = x_idx.flatten() * dx
    
    z_c, y_c, x_c = cp.mean(z_phys), cp.mean(y_phys), cp.mean(x_phys)
    z_shifted = z_phys - z_c
    y_shifted = y_phys - y_c
    x_shifted = x_phys - x_c
    
    r_phys = cp.sqrt(x_shifted**2 + y_shifted**2 + z_shifted**2)
    max_radius = float(cp.max(r_phys))
    
    # 3. GPU Synthesis
    print(f"Synthesizing {len(raw_moments)} basis functions on GPU...")
    start_time = time.time()
    
    f_v_complex_gpu = cp.zeros(len(z_shifted), dtype=cp.complex128)
    
    for key, val in raw_moments.items():
        n, l, m = map(int, key.split('_'))
        C = val[0] + 1j * val[1]
        
        Z = zernike_3d_basis_physical_gpu(n, l, m, x_shifted, y_shifted, z_shifted, max_radius)
        f_v_complex_gpu += C * Z
        
    end_time = time.time()
    print(f"GPU Synthesis time: {end_time - start_time:.2f} seconds")
    
    f_v_complex_cpu = f_v_complex_gpu.get()
    
    max_imag = np.max(np.abs(f_v_complex_cpu.imag))
    print(f"Maximum imaginary part (should be ~0): {max_imag:.4e}")
    
    recon_flat = f_v_complex_cpu.real
    recon_vol = recon_flat.reshape((z_dim, y_dim, x_dim))
    
    # 4. Metrics
    orig_flat = orig_vol.flatten()
    mse = np.mean((orig_flat - recon_flat)**2)
    r = np.corrcoef(orig_flat, recon_flat)[0, 1]
    
    print("\n========================================")
    print(f"  Reconstruction Verification (N={n_max})")
    print("========================================")
    print(f"Mean Squared Error     : {mse:.4f}")
    print(f"Pearson Correlation    : {r:.4f}")
    print("========================================\n")
    
    # 5. Napari Viewer
    print("Opening Napari to show results (blocking)...")
    viewer = napari.Viewer()
    
    scale = (dz, dy, dx)
    
    viewer.add_image(orig_vol, name='Original ch04', colormap='gray', scale=scale, blending='additive')
    viewer.add_image(recon_vol, name=f'Reconstructed (N={n_max})', colormap='magma', scale=scale, blending='additive')
    
    napari.run()

if __name__ == '__main__':
    main()
