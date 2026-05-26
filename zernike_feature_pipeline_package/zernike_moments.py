import numpy as np
import joblib
from zernike_basis import zernike_3d_basis_physical

def extract_valid_indices(n_max, max_functions=None):
    """
    Generate all valid (n, l, m) indices up to maximum degree n_max.
    """
    indices = []
    for n in range(n_max + 1):
        for l in range(n + 1):
            if (n - l) % 2 == 0:
                for m in range(-l, l + 1):
                    indices.append((n, l, m))
                    if max_functions and len(indices) == max_functions:
                        return indices
    return indices

def compute_zernike_moments(binary_mask, intensity_vol=None, n_max=5, max_functions=None, voxel_spacing=(1.0, 1.0, 1.0)):
    """
    Compute 3D Zernike moments for a volume using physical units.
    
    Parameters
    ----------
    binary_mask : np.ndarray
        3D boolean or integer array representing the shape (1 for object, 0 for background).
    intensity_vol : np.ndarray, optional
        3D array of intensities. If provided, the moments will expand the intensity field 
        rather than just the binary shape.
    n_max : int
        Maximum degree for Zernike moments.
    max_functions: int
        Max basis functions to compute.
    voxel_spacing : tuple
        Physical dimensions of voxels (dz, dy, dx) to properly scale coordinates.
        
    Returns
    -------
    dict
        Dictionary containing raw moments Omega_{nl}^m and invariants F_{nl}.
    """
    # Find all object voxels
    z_idx, y_idx, x_idx = np.nonzero(binary_mask)
    if len(z_idx) == 0:
        raise ValueError("Binary mask is empty.")
        
    if intensity_vol is not None:
        f_r = intensity_vol[z_idx, y_idx, x_idx].astype(np.float64)
    else:
        f_r = 1.0
        
    # Scale indices to physical coordinates using anisotropic spacing
    dz, dy, dx = voxel_spacing
    z_phys = z_idx * dz
    y_phys = y_idx * dy
    x_phys = x_idx * dx
    
    # Translate so the centroid is at the origin
    z_c, y_c, x_c = np.mean(z_phys), np.mean(y_phys), np.mean(x_phys)
    z_shifted = z_phys - z_c
    y_shifted = y_phys - y_c
    x_shifted = x_phys - x_c
    
    # Find bounding physical radius
    max_radius = np.max(np.sqrt(z_shifted**2 + y_shifted**2 + x_shifted**2))
    if max_radius == 0:
        max_radius = 1.0 # fallback for single voxel
    
    # True physical volume of a single voxel
    dV = dx * dy * dz
    
    moments = {}
    indices = extract_valid_indices(n_max, max_functions)
    
    print(f"Computing {len(indices)} moments up to degree {n_max}...")
    print(f"Using bounding physical radius: {max_radius:.4f} um, voxel dV: {dV:.6f} um^3")
    
    def _compute_single(idx, x_s, y_s, z_s, r_max, f_vol, dv_vol):
        n, l, m = idx
        basis_vals = zernike_3d_basis_physical(n, l, m, x_s, y_s, z_s, r_max)
        omega = np.sum(f_vol * np.conjugate(basis_vals)) * dv_vol
        return (idx, omega)
        
    import os
    num_workers = os.cpu_count() or 4
    print(f"Running parallel evaluation with {num_workers} processes (joblib)...")
    
    results = joblib.Parallel(n_jobs=num_workers)(
        joblib.delayed(_compute_single)(idx, x_shifted, y_shifted, z_shifted, max_radius, f_r, dV) 
        for idx in indices
    )
        
    for idx, omega in results:
        moments[idx] = omega
        
    # Compute rotationally invariant descriptors (F_{nl})
    invariants = {}
    for n in range(n_max + 1):
        for l in range(n + 1):
            if (n - l) % 2 == 0:
                # Sum of magnitude squared over all m
                norm_sq = 0.0
                for m in range(-l, l + 1):
                    omega = moments.get((n, l, m), 0.0)
                    norm_sq += np.abs(omega)**2
                # Some definitions take the L2 norm (sqrt), others use squared.
                invariants[(n, l)] = np.sqrt(norm_sq)
                
    return {'raw_moments': moments, 'invariants': invariants}

if __name__ == "__main__":
    # Test on a small cube
    mask = np.zeros((10, 10, 10))
    mask[3:7, 3:7, 3:7] = 1
    res = compute_zernike_moments(mask, n_max=2)
    print("Invariants F_{nl}:")
    for k, v in res['invariants'].items():
        print(f"  n={k[0]}, l={k[1]}: {v:.6f}")
