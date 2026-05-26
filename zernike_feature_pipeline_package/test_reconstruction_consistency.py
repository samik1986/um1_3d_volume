import numpy as np
from zernike_basis import zernike_3d_basis_physical

def make_real_coeffs(base_coeffs):
    """
    Given a set of base coefficients, generate the full set of coefficients
    that ensures the reconstructed volume is strictly real.
    Condition: C_{nl}^{-m} = (-1)^m * (C_{nl}^m)^*
    """
    coeffs = {}
    for (n, l, m), val in base_coeffs.items():
        coeffs[(n, l, m)] = val
        if m != 0:
            coeffs[(n, l, -m)] = ((-1)**m) * np.conjugate(val)
    return coeffs

def run_consistency_test():
    # 1. Setup physical units matching the current problem
    spacing_z, spacing_y, spacing_x = 0.5, 0.1102, 0.1102
    dV = spacing_z * spacing_y * spacing_x
    max_radius = 5.0  # um
    
    # Create grid large enough to contain the sphere
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
    
    print(f"Grid size: {grid_z}x{grid_y}x{grid_x}")
    print(f"Voxel Spacing: z={spacing_z}, y={spacing_y}, x={spacing_x} um")
    print(f"Active Voxels (R <= {max_radius}): {np.sum(valid)}")
    print(f"Physical dV: {dV:.6f} um^3\n")
    
    # 2. Define known base coefficients
    base_coeffs = {
        (0, 0, 0): 2.0 + 0j,
        (1, 1, 1): 1.5 + 0.5j,
        (2, 0, 0): -1.0 + 0j,
        (2, 2, 2): 0.8 - 0.4j,
        (3, 1, 1): -0.5 + 0.3j,
        (3, 3, 3): 0.2 + 0.7j,
    }
    
    true_coeffs = make_real_coeffs(base_coeffs)
    print(f"Number of non-zero Zernike coefficients: {len(true_coeffs)}")
    
    # 3. Construct the test function
    f_v_complex = np.zeros_like(x_v, dtype=np.complex128)
    for (n, l, m), C in true_coeffs.items():
        Z = zernike_3d_basis_physical(n, l, m, x_v, y_v, z_v, max_radius)
        f_v_complex += C * Z
        
    # Check that imaginary part is effectively zero
    max_imag = np.max(np.abs(f_v_complex.imag))
    print(f"Maximum imaginary part of constructed volume: {max_imag:.4e}")
    assert max_imag < 1e-10, "Constructed volume is not real!"
    
    # Take real part
    f_v = f_v_complex.real
    
    # 4. Apply Zernike Decomposition to extract coefficients
    extracted_coeffs = {}
    for (n, l, m) in true_coeffs.keys():
        Z = zernike_3d_basis_physical(n, l, m, x_v, y_v, z_v, max_radius)
        Omega = np.sum(f_v * np.conjugate(Z)) * dV
        extracted_coeffs[(n, l, m)] = Omega
        
    # 5. Check if extracted matches true
    print("\n--- Coefficient Comparison ---")
    print(f"{'n, l, m':<10} | {'True Coeff':<25} | {'Extracted Coeff':<25} | {'Diff':<15}")
    print("-" * 80)
    for k in true_coeffs.keys():
        t = true_coeffs[k]
        e = extracted_coeffs[k]
        diff = np.abs(t - e)
        print(f"{str(k):<10} | {t.real:>8.4f} + {t.imag:>8.4f}j | {e.real:>8.4f} + {e.imag:>8.4f}j | {diff:.4e}")
        
    # 6. Check Parseval's Theorem
    print("\n--- Parseval's Theorem Verification ---")
    
    # Signal Energy: Integral of |f|^2 dV
    signal_energy = np.sum(f_v**2) * dV
    
    # Spectral Energy (True): Sum of |C|^2
    spectral_energy_true = sum(np.abs(C)**2 for C in true_coeffs.values())
    
    # Spectral Energy (Extracted): Sum of |Omega|^2
    spectral_energy_extracted = sum(np.abs(Omega)**2 for Omega in extracted_coeffs.values())
    
    print(f"Signal Energy (Integral |f|^2 dV)     : {signal_energy:.6f}")
    print(f"Spectral Energy (Sum |True|^2)        : {spectral_energy_true:.6f}")
    print(f"Spectral Energy (Sum |Extracted|^2)   : {spectral_energy_extracted:.6f}")
    
    pct_err_true = abs(signal_energy - spectral_energy_true) / spectral_energy_true * 100
    pct_err_extr = abs(signal_energy - spectral_energy_extracted) / spectral_energy_extracted * 100
    
    print(f"Difference (Signal vs True)           : {pct_err_true:.4e} %")
    print(f"Difference (Signal vs Extracted)      : {pct_err_extr:.4e} %")
    print("\nNote: Small discrepancies are expected due to grid discretization and voxel integration approximation.")

if __name__ == '__main__':
    run_consistency_test()
