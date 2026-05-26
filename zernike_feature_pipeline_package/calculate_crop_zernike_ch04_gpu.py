import os
import json
import time
import math
import numpy as np
import cupy as cp
import tifffile
from zernike_basis_gpu import zernike_3d_basis_physical_gpu

def extract_valid_indices(n_max, max_functions=None):
    indices = []
    for n in range(n_max + 1):
        for l in range(n + 1):
            if (n - l) % 2 == 0:
                for m in range(-l, l + 1):
                    indices.append((n, l, m))
                    
    if max_functions is not None:
        return indices[:max_functions]
    return indices

def compute_zernike_moments_gpu(intensity_vol, voxel_spacing, n_max=10, max_functions=None):
    """
    Compute Zernike moments using GPU acceleration via CuPy.
    """
    z_dim, y_dim, x_dim = intensity_vol.shape
    dz, dy, dx = voxel_spacing
    dV = dz * dy * dx
    
    # 1. Transfer image to GPU
    print("Transferring volume to GPU memory...")
    f_vol_gpu = cp.asarray(intensity_vol, dtype=cp.float64)
    
    # 2. Build physical coordinates on GPU
    print("Building coordinate grids on GPU...")
    z_idx, y_idx, x_idx = cp.indices((z_dim, y_dim, x_dim))
    
    z_phys = z_idx.flatten() * dz
    y_phys = y_idx.flatten() * dy
    x_phys = x_idx.flatten() * dx
    
    # Centroid (geometric center)
    z_c, y_c, x_c = cp.mean(z_phys), cp.mean(y_phys), cp.mean(x_phys)
    z_shifted = z_phys - z_c
    y_shifted = y_phys - y_c
    x_shifted = x_phys - x_c
    
    f_flat_gpu = f_vol_gpu.flatten()
    
    # Calculate bounding sphere radius
    r_phys = cp.sqrt(x_shifted**2 + y_shifted**2 + z_shifted**2)
    max_radius = float(cp.max(r_phys))
    
    print("Precomputing spherical coordinate grids...")
    rho = r_phys / max_radius
    
    theta = cp.zeros_like(r_phys)
    mask = r_phys > 0
    theta[mask] = cp.arccos(cp.clip(z_shifted[mask] / r_phys[mask], -1.0, 1.0))
    
    phi = cp.arctan2(y_shifted, x_shifted)
    
    # We no longer need the Cartesian shifts to save VRAM
    del x_shifted, y_shifted, z_shifted, r_phys
    cp.get_default_memory_pool().free_all_blocks()
    
    # 3. Compute moments
    indices = extract_valid_indices(n_max, max_functions)
    moments = {}
    
    print(f"Computing {len(indices)} moments up to degree {n_max} on GPU...")
    print(f"Using bounding physical radius: {max_radius:.4f} um, voxel dV: {dV:.6f} um^3")
    
    from zernike_basis_gpu import zernike_spherical_gpu, zernike_radial_gpu
    
    start_time = time.time()
    
    # Group indices by (n, l) so we only calculate R_nl once per group
    grouped_indices = {}
    for (n, l, m) in indices:
        if (n, l) not in grouped_indices:
            grouped_indices[(n, l)] = []
        grouped_indices[(n, l)].append(m)
        
    for (n, l), m_list in grouped_indices.items():
        # Compute R_nl once
        R_nl = zernike_radial_gpu(n, l, rho)
        
        # Precompute the strictly real component: f(r) * R_nl * dV
        W_nl = f_flat_gpu * R_nl * dV
        norm_factor = math.sqrt((2 * n + 3) / (max_radius**3))
        
        for m in m_list:
            # Evaluate just the spherical harmonic
            Y = zernike_spherical_gpu(l, m, theta, phi)
            
            # vdot(a, b) computes dot(conjugate(a), b). 
            # So vdot(Y, W_nl) is exactly Sum( Y* * W_nl )
            dot_val = cp.vdot(Y, W_nl)
            
            omega_gpu = norm_factor * dot_val
            # Pull scalar result back to CPU
            moments[(n, l, m)] = complex(omega_gpu)
            
    end_time = time.time()
    print(f"GPU Execution time: {end_time - start_time:.2f} seconds")
    
    return moments, max_radius

def main():
    target = 'crop_001_ch04'
    n_max = 40  # Massive extraction up to N=40 (11,480 functions)
    
    base_dir = r'c:\Users\banerjee\Desktop\um1_3d_volume\neuron_processing\output\custom_crops'
    tif_path = os.path.join(base_dir, f'{target}.tif')
    out_json = os.path.join(base_dir, f'{target}_intensity_zernike_gpu_n40.json')
    
    print(f"Loading {tif_path}...")
    intensity_vol = tifffile.imread(tif_path).astype(np.float64)
    voxel_spacing = (0.5, 0.1102, 0.1102)
    
    print(f"Computing Zernike expansion for the FULL {target} intensity volume on GPU...")
    moments, max_radius = compute_zernike_moments_gpu(
        intensity_vol, 
        voxel_spacing, 
        n_max=n_max,
        max_functions=None
    )
    
    # Group invariants
    F_nl = {}
    for (n, l, m), omega in moments.items():
        if m >= 0:
            key = f"F_{n}_{l}"
            mag_sq = abs(omega)**2
            if m > 0:
                mag_sq *= 2  # Account for negative m symmetry
            F_nl[key] = F_nl.get(key, 0.0) + mag_sq
            
    for key in F_nl:
        F_nl[key] = np.sqrt(F_nl[key])
        
    raw_moments = {f"{n}_{l}_{m}": [float(val.real), float(val.imag)] for (n, l, m), val in moments.items()}
    
    output = {
        "metadata": {
            "target": f"gpu_{target}",
            "n_max": n_max,
            "max_functions": None,
            "voxel_spacing_um": voxel_spacing,
            "volume_voxels": intensity_vol.size,
            "max_radius": max_radius
        },
        "invariants": F_nl,
        "raw_moments": raw_moments
    }
    
    with open(out_json, 'w') as f:
        json.dump(output, f, indent=2)
        
    print(f"Structured descriptors saved to {out_json}")

if __name__ == '__main__':
    main()
