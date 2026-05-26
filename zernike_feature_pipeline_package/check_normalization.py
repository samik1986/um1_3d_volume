import numpy as np
from zernike_basis import zernike_3d_basis_physical

def check_normalization():
    print("Testing physical Zernike 3D Basis normalization...")
    
    # Create a dense 3D grid in physical coordinates
    # Let's say R_max = 5.0 um
    R_max = 5.0
    grid_size = 120
    lin = np.linspace(-R_max, R_max, grid_size)
    
    # Calculate physical voxel volume
    dx = lin[1] - lin[0]
    dV = dx**3
    
    z_g, y_g, x_g = np.meshgrid(lin, lin, lin, indexing='ij')
    r_g = np.sqrt(z_g**2 + y_g**2 + x_g**2)
    
    # Mask to physical sphere (only integrate within r <= R_max)
    valid = r_g <= R_max
    x_v = x_g[valid]
    y_v = y_g[valid]
    z_v = z_g[valid]
    
    test_funcs = [
        (0, 0, 0),
        (1, 1, 0),
        (1, 1, -1),
        (2, 2, 2),
        (3, 1, 0),
        (4, 2, -2)
    ]
    
    for (n, l, m) in test_funcs:
        basis = zernike_3d_basis_physical(n, l, m, x_v, y_v, z_v, R_max)
        
        # Integral of |Z|^2 over the physical sphere
        raw_integral = np.sum(np.abs(basis)**2) * dV
        
        print(f"\nBasis Z(n={n}, l={l}, m={m}):")
        print(f"  Physical Integral |Z|^2 dV_phys = {raw_integral:.5f}  (Expected exactly 1.0)")

if __name__ == "__main__":
    check_normalization()
