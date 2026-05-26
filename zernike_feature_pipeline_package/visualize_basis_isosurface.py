import numpy as np
import napari
from zernike_basis import zernike_3d_basis

def generate_basis_volume(n, l, m, grid_size=64):
    """
    Generates a 3D grid containing the evaluated complex Zernike basis function.
    """
    lin = np.linspace(-1, 1, grid_size)
    z_g, y_g, x_g = np.meshgrid(lin, lin, lin, indexing='ij')
    r_g = np.sqrt(z_g**2 + y_g**2 + x_g**2)
    valid = r_g <= 1.0
    
    basis_vol = np.zeros_like(z_g, dtype=complex)
    basis_vol[valid] = zernike_3d_basis(n, l, m, x_g[valid], y_g[valid], z_g[valid])
    
    return basis_vol

def add_basis_to_viewer(viewer, n, l, m, grid_size=64):
    """
    Evaluates and adds the real and imaginary components of a Zernike basis function 
    to the Napari viewer as isosurfaces.
    """
    print(f"Generating Z_{n}_{l}^{m}...")
    basis_vol = generate_basis_volume(n, l, m, grid_size)
    basis_real = np.real(basis_vol)
    basis_imag = np.imag(basis_vol)
    
    # Spherical harmonics have positive and negative lobes.
    # We separate them to render distinct isosurfaces for positive and negative values.
    
    # Real components
    pos_real = np.clip(basis_real, 0, None)
    if np.max(pos_real) > 1e-5:
        viewer.add_image(pos_real, name=f'Z_{n}_{l}^{m} (Real +)', colormap='red', 
                         rendering='iso', iso_threshold=np.max(pos_real)*0.3, blending='additive')
        
    neg_real = np.clip(-basis_real, 0, None)
    if np.max(neg_real) > 1e-5:
        viewer.add_image(neg_real, name=f'Z_{n}_{l}^{m} (Real -)', colormap='blue', 
                         rendering='iso', iso_threshold=np.max(neg_real)*0.3, blending='additive')
        
    # Imaginary components
    pos_imag = np.clip(basis_imag, 0, None)
    if np.max(pos_imag) > 1e-5:
        viewer.add_image(pos_imag, name=f'Z_{n}_{l}^{m} (Imag +)', colormap='green', 
                         rendering='iso', iso_threshold=np.max(pos_imag)*0.3, blending='additive')
        
    neg_imag = np.clip(-basis_imag, 0, None)
    if np.max(neg_imag) > 1e-5:
        viewer.add_image(neg_imag, name=f'Z_{n}_{l}^{m} (Imag -)', colormap='magenta', 
                         rendering='iso', iso_threshold=np.max(neg_imag)*0.3, blending='additive')

def main():
    # Define the basis functions to visualize (l=2, all m, n up to 4)
    functions_to_visualize = []
    l = 2
    n_max = 4
    for n in range(l, n_max + 1, 2):  # n-l must be even
        for m in range(-l, l + 1):
            functions_to_visualize.append((n, l, m))
    
    viewer = napari.Viewer(title="Zernike Basis Isosurfaces")
    
    # Make a reference sphere wireframe just to see the boundary
    grid_size = 64
    lin = np.linspace(-1.1, 1.1, grid_size)
    z, y, x = np.meshgrid(lin, lin, lin, indexing='ij')
    r = np.sqrt(z**2 + y**2 + x**2)
    shell = (r >= 0.95) & (r <= 1.05)
    viewer.add_image(shell.astype(float), name='Unit Sphere', colormap='gray', 
                     blending='additive', opacity=0.1)

    for (n, l, m) in functions_to_visualize:
        add_basis_to_viewer(viewer, n, l, m, grid_size=grid_size)
        
    # Set the viewer to 3D mode automatically
    viewer.dims.ndisplay = 3
        
    napari.run()

if __name__ == "__main__":
    main()
