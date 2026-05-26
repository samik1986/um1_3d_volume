import numpy as np
from scipy.special import sph_harm

def zernike_spherical(l, m, theta, phi):
    """
    Evaluate the Spherical Harmonic Y_l^m(theta, phi).
    
    Parameters
    ----------
    l : int
        Degree of the harmonic (l >= 0).
    m : int
        Order of the harmonic (-l <= m <= l).
    theta : np.ndarray
        Polar angle in radians [0, pi].
    phi : np.ndarray
        Azimuthal angle in radians [0, 2*pi].
        
    Returns
    -------
    np.ndarray
        Evaluated complex spherical harmonic values.
        
    Notes
    -----
    In scipy's sph_harm signature, the order of angles is (m, n, theta, phi) 
    where theta is the azimuthal angle [0, 2pi] and phi is the polar angle [0, pi].
    We wrap this to use standard physics notation where theta is polar [0, pi]
    and phi is azimuthal [0, 2pi].
    """
    if abs(m) > l:
        raise ValueError("Order m must be in the range [-l, l].")
        
    # Scipy sph_harm signature: sph_harm(m, n, theta, phi)
    # n is degree (our l), m is order (our m)
    # theta in scipy is azimuthal (our phi), phi in scipy is polar (our theta)
    return sph_harm(m, l, phi, theta)

if __name__ == "__main__":
    # Test
    theta_test = np.array([0, np.pi/2, np.pi])
    phi_test = np.array([0, np.pi, 2*np.pi])
    print("Y_1^0:", zernike_spherical(1, 0, theta_test, phi_test))
