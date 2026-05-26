import numpy as np
from zernike_radial import zernike_radial
from zernike_spherical import zernike_spherical

def zernike_3d_basis_physical(n, l, m, x_phys, y_phys, z_phys, R_max):
    """
    Evaluate the full 3D Zernike polynomial Z_{nl}^m on physical coordinates.
    
    Parameters
    ----------
    n : int
        Degree (n >= 0).
    l : int
        Order (0 <= l <= n, and n - l is even).
    m : int
        Azimuthal index (-l <= m <= l).
    x_phys, y_phys, z_phys : np.ndarray
        Physical Cartesian coordinates.
    R_max : float
        Physical radius of the bounding sphere.
        
    Returns
    -------
    np.ndarray
        Complex values of the Zernike polynomial at each point, normalized such that
        the volumetric integral of the squared magnitude over the sphere evaluates to 1.
    """
    # Convert Physical Cartesian to Spherical coordinates
    r_phys = np.sqrt(x_phys**2 + y_phys**2 + z_phys**2)
    
    # Normalized radial distance rho in [0, 1]
    rho = r_phys / R_max
    
    # theta (polar angle) in [0, pi]
    # Handle origin safely to avoid division by zero
    theta = np.zeros_like(r_phys)
    mask = r_phys > 0
    theta[mask] = np.arccos(np.clip(z_phys[mask] / r_phys[mask], -1.0, 1.0))
    
    # phi (azimuthal angle) in [-pi, pi]
    phi = np.arctan2(y_phys, x_phys)
    
    # Evaluate radial and spherical components
    R = zernike_radial(n, l, rho)
    Y = zernike_spherical(l, m, theta, phi)
    
    # Enforce orthonormality over the physical sphere volume: \int |Z|^2 dV_phys = 1
    norm_factor = np.sqrt((2 * n + 3) / (R_max**3))
    
    return norm_factor * R * Y

if __name__ == "__main__":
    # Test
    x = np.array([0.0, 0.5, 0.0])
    y = np.array([0.0, 0.5, 0.0])
    z = np.array([0.0, 0.0, 0.5])
    print("Z_20^0:", zernike_3d_basis(2, 0, 0, x, y, z))
