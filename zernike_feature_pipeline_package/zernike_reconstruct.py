import numpy as np
from zernike_basis import zernike_3d_basis
from zernike_moments import extract_valid_indices

def reconstruct_zernike_volume(grid_size, moments, n_max):
    """
    Compute the inverse Zernike transform over a 3D grid.
    
    Parameters
    ----------
    grid_size : int
        The size of the 3D grid along each dimension (grid_size x grid_size x grid_size).
    moments : dict
        A dictionary of raw complex moments with keys as strings "n_l_m" or tuples (n,l,m).
    n_max : int
        Maximum degree N used for the reconstruction.
        
    Returns
    -------
    np.ndarray
        A 3D grid containing the reconstructed scalar field (density).
    """
    # Create coordinate grid from -1 to 1
    lin = np.linspace(-1, 1, grid_size)
    z_grid, y_grid, x_grid = np.meshgrid(lin, lin, lin, indexing='ij')
    
    # Mask out coordinates outside the unit sphere
    r_sq = z_grid**2 + y_grid**2 + x_grid**2
    valid_mask = r_sq <= 1.0
    
    z_valid = z_grid[valid_mask]
    y_valid = y_grid[valid_mask]
    x_valid = x_grid[valid_mask]
    
    # Reconstructed values for valid voxels
    recon_valid = np.zeros(z_valid.shape, dtype=complex)
    
    indices = extract_valid_indices(n_max)
    for (n, l, m) in indices:
        # Get moment from either tuple or string key
        key_tuple = (n, l, m)
        key_str = f"{n}_{l}_{m}"
        
        if key_tuple in moments:
            omega = moments[key_tuple]
        elif key_str in moments:
            val = moments[key_str]
            omega = complex(val[0], val[1])
        else:
            omega = 0.0 + 0.0j
            
        if omega == 0.0 + 0.0j:
            continue
            
        basis_vals = zernike_3d_basis(n, l, m, x_valid, y_valid, z_valid)
        recon_valid += omega * basis_vals
        
    # The original shape should be purely real, but due to approximation it might have a small imaginary component.
    recon_valid = np.real(recon_valid)
    
    # Map back to full grid
    volume = np.zeros(z_grid.shape, dtype=float)
    volume[valid_mask] = recon_valid
    
    return volume
