import numpy as np
from zernike_basis import zernike_3d_basis_physical
import scipy.integrate as integrate
import time

def make_real_coeffs(base_coeffs):
    coeffs = {}
    for (n, l, m), val in base_coeffs.items():
        coeffs[(n, l, m)] = val
        if m != 0:
            coeffs[(n, l, -m)] = ((-1)**m) * np.conjugate(val)
    return coeffs

def run_integration_test():
    spacing_z, spacing_y, spacing_x = 0.5, 0.1102, 0.1102
    dV = spacing_z * spacing_y * spacing_x
    max_radius = 5.0
    
    grid_z = int(2 * max_radius / spacing_z) + 5
    grid_y = int(2 * max_radius / spacing_y) + 5
    grid_x = int(2 * max_radius / spacing_x) + 5
    
    z = (np.arange(grid_z) - grid_z // 2) * spacing_z
    y = (np.arange(grid_y) - grid_y // 2) * spacing_y
    x = (np.arange(grid_x) - grid_x // 2) * spacing_x
    
    z_g, y_g, x_g = np.meshgrid(z, y, x, indexing='ij')
    r_g = np.sqrt(z_g**2 + y_g**2 + x_g**2)
    
    valid = r_g <= max_radius
    z_v = z_g[valid]
    y_v = y_g[valid]
    x_v = x_g[valid]
    
    base_coeffs = {
        (0, 0, 0): 2.0 + 0j,
        (1, 1, 1): 1.5 + 0.5j,
        (2, 0, 0): -1.0 + 0j,
    }
    true_coeffs = make_real_coeffs(base_coeffs)
    
    f_v_complex = np.zeros_like(x_v, dtype=np.complex128)
    for (n, l, m), C in true_coeffs.items():
        Z = zernike_3d_basis_physical(n, l, m, x_v, y_v, z_v, max_radius)
        f_v_complex += C * Z
        
    f_v = f_v_complex.real
    
    # 1. Riemann Sum (Midpoint)
    extracted_riemann = {}
    for (n, l, m) in true_coeffs.keys():
        Z = zernike_3d_basis_physical(n, l, m, x_v, y_v, z_v, max_radius)
        extracted_riemann[(n, l, m)] = np.sum(f_v * np.conjugate(Z)) * dV

    # 2. Trapezoidal Rule
    extracted_trapz = {}
    for (n, l, m) in true_coeffs.keys():
        Z = zernike_3d_basis_physical(n, l, m, x_v, y_v, z_v, max_radius)
        
        integrand_grid = np.zeros_like(r_g, dtype=np.complex128)
        integrand_grid[valid] = f_v * np.conjugate(Z)
        
        # Integrate over x, then y, then z
        val = integrate.trapezoid(
                integrate.trapezoid(
                    integrate.trapezoid(integrand_grid, x=x, axis=2),
                x=y, axis=1),
              x=z, axis=0)
        extracted_trapz[(n, l, m)] = val

    # 3. Simpson's Rule
    extracted_simp = {}
    for (n, l, m) in true_coeffs.keys():
        Z = zernike_3d_basis_physical(n, l, m, x_v, y_v, z_v, max_radius)
        
        integrand_grid = np.zeros_like(r_g, dtype=np.complex128)
        integrand_grid[valid] = f_v * np.conjugate(Z)
        
        val = integrate.simpson(
                integrate.simpson(
                    integrate.simpson(integrand_grid, x=x, axis=2),
                x=y, axis=1),
              x=z, axis=0)
        extracted_simp[(n, l, m)] = val
        
    # 4. Soft fractional boundary mask (Riemann with super-sampling on boundary)
    # Generate a super-sampled mask (3x3x3 per voxel) to compute a fractional mask
    sub_div = 3
    sub_z = np.linspace(-spacing_z/2, spacing_z/2, sub_div)
    sub_y = np.linspace(-spacing_y/2, spacing_y/2, sub_div)
    sub_x = np.linspace(-spacing_x/2, spacing_x/2, sub_div)
    sub_weight = np.zeros_like(r_g, dtype=np.float64)
    
    print("Computing soft mask...")
    for sz in sub_z:
        for sy in sub_y:
            for sx in sub_x:
                sub_r = np.sqrt((z_g + sz)**2 + (y_g + sy)**2 + (x_g + sx)**2)
                sub_weight += (sub_r <= max_radius).astype(float)
    sub_weight /= (sub_div**3)
    
    # We re-evaluate f_v and Z everywhere to use the soft mask
    f_grid = np.zeros_like(r_g, dtype=np.complex128)
    for (n, l, m), C in true_coeffs.items():
        Z = zernike_3d_basis_physical(n, l, m, x_g, y_g, z_g, max_radius)
        f_grid += C * Z
    f_grid = f_grid.real
    
    extracted_soft = {}
    for (n, l, m) in true_coeffs.keys():
        Z = zernike_3d_basis_physical(n, l, m, x_g, y_g, z_g, max_radius)
        val = np.sum(f_grid * np.conjugate(Z) * sub_weight) * dV
        extracted_soft[(n, l, m)] = val

    print("\n--- Error Comparison (|True - Extracted|) ---")
    print(f"{'n, l, m':<10} | {'Riemann':<12} | {'Trapezoid':<12} | {'Simpson':<12} | {'Soft Mask':<12}")
    print("-" * 75)
    for k in true_coeffs.keys():
        t = true_coeffs[k]
        err_riem = np.abs(t - extracted_riemann[k])
        err_trap = np.abs(t - extracted_trapz[k])
        err_simp = np.abs(t - extracted_simp[k])
        err_soft = np.abs(t - extracted_soft[k])
        print(f"{str(k):<10} | {err_riem:10.4f} | {err_trap:10.4f} | {err_simp:10.4f} | {err_soft:10.4f}")

if __name__ == '__main__':
    run_integration_test()
