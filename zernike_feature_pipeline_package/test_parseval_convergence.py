import numpy as np
import time
from zernike_basis import zernike_3d_basis_physical
from zernike_moments import extract_valid_indices

def compute_convergence():
    grid_size = 41
    max_radius = 20.0
    lin = np.linspace(-max_radius, max_radius, grid_size)
    dx = lin[1] - lin[0]
    dV = dx**3
    
    z_g, y_g, x_g = np.meshgrid(lin, lin, lin, indexing='ij')
    r_g = np.sqrt(z_g**2 + y_g**2 + x_g**2)
    
    # Test Volume 1: Binary Sphere (Sharp edges, hard to fit)
    # This simulates a segmented cell mask.
    test_vol_binary = np.zeros_like(r_g)
    test_vol_binary[r_g <= 12.0] = 1.0
    
    # Test Volume 2: Gaussian Blob (Smooth edges, easy to fit)
    # This simulates a smooth fluorescence signal.
    sigma = 6.0
    test_vol_smooth = np.exp(-(r_g**2) / (2 * sigma**2))
    
    valid = r_g <= max_radius
    z_v = z_g[valid]
    y_v = y_g[valid]
    x_v = x_g[valid]
    
    f_binary = test_vol_binary[valid]
    f_smooth = test_vol_smooth[valid]
    
    total_energy_binary = np.sum(f_binary**2) * dV
    total_energy_smooth = np.sum(f_smooth**2) * dV
    
    n_max_test = 20
    indices = extract_valid_indices(n_max_test)
    
    print(f"Testing Parseval's convergence up to N = {n_max_test} (Total {len(indices)} polynomials)")
    print(f"Number of evaluation voxels: {len(x_v)}")
    print("-" * 50)
    print(f"Total True Energy (Binary Sphere) : {total_energy_binary:.4f}")
    print(f"Total True Energy (Smooth Blob)   : {total_energy_smooth:.4f}")
    print("-" * 50)
    
    moments_binary = {}
    moments_smooth = {}
    
    start_time = time.time()
    
    for (n, l, m) in indices:
        basis_vals = zernike_3d_basis_physical(n, l, m, x_v, y_v, z_v, max_radius)
        
        omega_bin = np.sum(f_binary * np.conjugate(basis_vals)) * dV
        moments_binary[(n, l, m)] = omega_bin
        
        omega_smooth = np.sum(f_smooth * np.conjugate(basis_vals)) * dV
        moments_smooth[(n, l, m)] = omega_smooth
        
    print(f"Evaluated all {len(indices)} polynomials in {time.time()-start_time:.2f} seconds.\n")
    print(f"{'N':<4} | {'Binary Energy (%)':<20} | {'Smooth Energy (%)':<20}")
    print("-" * 50)
    
    current_en_bin = 0.0
    current_en_smooth = 0.0
    
    for n_curr in range(n_max_test + 1):
        for (n, l, m) in indices:
            if n == n_curr:
                current_en_bin += np.abs(moments_binary[(n, l, m)])**2
                current_en_smooth += np.abs(moments_smooth[(n, l, m)])**2
        
        pct_bin = (current_en_bin / total_energy_binary) * 100
        pct_smooth = (current_en_smooth / total_energy_smooth) * 100
        
        print(f"{n_curr:<4} | {pct_bin:>12.2f} %       | {pct_smooth:>12.2f} %")

if __name__ == '__main__':
    compute_convergence()
