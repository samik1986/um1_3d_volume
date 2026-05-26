import math
import numpy as np
from scipy.special import gamma

def _q_coeff(n, l, nu):
    """
    Calculate the coefficient Q_{nl\nu} for the 3D Zernike radial polynomial.
    """
    # Numerator: (-1)^nu * (n - nu)!
    num = ((-1)**nu) * math.factorial(n - nu)
    
    # Denominator: nu! * ((n+l)/2 - nu)! * ((n-l)/2 - nu)!
    den = math.factorial(nu) * \
          math.factorial((n + l) // 2 - nu) * \
          math.factorial((n - l) // 2 - nu)
          
    return num / den

def zernike_radial(n, l, r):
    """
    Evaluate the 3D Zernike radial polynomial R_{nl}(r).
    
    Parameters
    ----------
    n : int
        Degree of the polynomial (n >= 0).
    l : int
        Order of the polynomial (0 <= l <= n, and n - l is even).
    r : np.ndarray
        Radial distances (usually r <= 1.0).
        
    Returns
    -------
    np.ndarray
        Evaluated radial polynomial values at r.
    """
    if (n - l) % 2 != 0:
        raise ValueError("n - l must be even for 3D Zernike radial polynomials.")
    if l < 0 or l > n:
        raise ValueError("Order l must be between 0 and n.")
        
    R = np.zeros_like(r, dtype=float)
    
    k_max = (n - l) // 2
    for nu in range(k_max + 1):
        coeff = _q_coeff(n, l, nu)
        power = n - 2 * nu
        R += coeff * (r ** power)
        
    return R

if __name__ == "__main__":
    # Test
    r_test = np.linspace(0, 1, 5)
    print("R_20(r):", zernike_radial(2, 0, r_test))
