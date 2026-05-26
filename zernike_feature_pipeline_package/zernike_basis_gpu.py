import math
import cupy as cp
from cupyx.scipy.special import sph_harm

def _q_coeff(n, l, nu):
    """
    Calculate the coefficient Q_{nl\nu} for the 3D Zernike radial polynomial.
    Uses standard python math since n, l, nu are small scalars.
    """
    num = ((-1)**nu) * math.factorial(n - nu)
    den = math.factorial(nu) * \
          math.factorial((n + l) // 2 - nu) * \
          math.factorial((n - l) // 2 - nu)
    return num / den

def zernike_radial_gpu(n, l, r):
    """
    Evaluate the 3D Zernike radial polynomial R_{nl}(r) on the GPU.
    r is a cupy array.
    """
    if (n - l) % 2 != 0:
        raise ValueError("n - l must be even for 3D Zernike radial polynomials.")
    if l < 0 or l > n:
        raise ValueError("Order l must be between 0 and n.")
        
    R = cp.zeros_like(r, dtype=cp.float64)
    
    k_max = (n - l) // 2
    for nu in range(k_max + 1):
        coeff = _q_coeff(n, l, nu)
        power = n - 2 * nu
        R += coeff * (r ** power)
        
    return R

def zernike_spherical_gpu(l, m, theta, phi):
    """
    Evaluate the Spherical Harmonic Y_l^m(theta, phi) on the GPU.
    theta and phi are cupy arrays.
    """
    if abs(m) > l:
        raise ValueError("Order m must be in the range [-l, l].")
        
    # cupyx.scipy.special.sph_harm signature matches scipy
    return sph_harm(m, l, phi, theta)

def zernike_3d_basis_physical_gpu(n, l, m, x_phys, y_phys, z_phys, R_max):
    """
    Evaluate the full 3D Zernike polynomial Z_{nl}^m on physical coordinates using GPU.
    """
    r_phys = cp.sqrt(x_phys**2 + y_phys**2 + z_phys**2)
    rho = r_phys / R_max
    
    # theta (polar angle) in [0, pi]
    theta = cp.zeros_like(r_phys)
    mask = r_phys > 0
    theta[mask] = cp.arccos(cp.clip(z_phys[mask] / r_phys[mask], -1.0, 1.0))
    
    # phi (azimuthal angle) in [-pi, pi]
    phi = cp.arctan2(y_phys, x_phys)
    
    # Evaluate components
    R = zernike_radial_gpu(n, l, rho)
    Y = zernike_spherical_gpu(l, m, theta, phi)
    
    norm_factor = math.sqrt((2 * n + 3) / (R_max**3))
    
    return norm_factor * R * Y

def zernike_3d_basis_precomputed_gpu(n, l, m, rho, theta, phi, R_max, R_cached=None):
    """
    Evaluate the Zernike polynomial using highly-optimized precomputed spherical coordinates.
    Optionally accepts a precomputed radial array R_cached to avoid redundant recalculation.
    """
    if R_cached is not None:
        R = R_cached
    else:
        R = zernike_radial_gpu(n, l, rho)
        
    Y = zernike_spherical_gpu(l, m, theta, phi)
    
    norm_factor = math.sqrt((2 * n + 3) / (R_max**3))
    
    return norm_factor * R * Y
