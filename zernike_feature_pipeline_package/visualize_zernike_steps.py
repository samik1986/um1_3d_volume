import os
import json
import numpy as np
import tifffile
import napari
from skimage.measure import regionprops
from zernike_reconstruct import reconstruct_zernike_volume
from zernike_basis import zernike_3d_basis

def generate_unit_sphere_boundary(grid_size):
    lin = np.linspace(-1.1, 1.1, grid_size)
    z, y, x = np.meshgrid(lin, lin, lin, indexing='ij')
    r = np.sqrt(z**2 + y**2 + x**2)
    # create a thin shell
    shell = (r >= 0.95) & (r <= 1.05)
    return shell, lin

def main():
    # 1. Load cell mask
    crop_dir = r'c:\Users\banerjee\Desktop\um1_3d_volume\neuron_processing\output\custom_crops'
    labels_path = os.path.join(crop_dir, 'crop_001_labels.tif')
    json_path = os.path.join(crop_dir, 'crop_001_cell_2521_zernike.json')
    
    if not os.path.exists(json_path):
        print("Waiting for JSON calculation to finish. Please try again later.")
        return
        
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    cell_id = data["metadata"]["cell_id"]
    n_max = data["metadata"]["n_max"]
    voxel_spacing = data["metadata"]["voxel_spacing_um"]
    raw_moments = data["raw_moments"]
    
    labels_vol = tifffile.imread(labels_path)
    mask = (labels_vol == cell_id).astype(np.uint8)
    
    # 2. Extract bounding box to isolate view
    props = regionprops(mask)[0]
    bz, by, bx, Bz, By, Bx = props.bbox
    # Add some padding
    pad = 5
    bz, Bz = max(0, bz-pad), min(mask.shape[0], Bz+pad)
    by, By = max(0, by-pad), min(mask.shape[1], By+pad)
    bx, Bx = max(0, bx-pad), min(mask.shape[2], Bx+pad)
    
    submask = mask[bz:Bz, by:By, bx:Bx]
    
    # 3. Create Grid corresponding to the scaled space (for reconstruction)
    # The reconstruction was done on a normalized [-1, 1] grid.
    print("Reconstructing Zernike volume from moments...")
    grid_size = 64
    reconstructed_vol = reconstruct_zernike_volume(grid_size, raw_moments, n_max)
    
    # 4. Generate Basis Function Volume for Visualization (e.g. Z_{1,1}^1)
    print("Generating Basis Function Z_1_1^1...")
    lin = np.linspace(-1, 1, grid_size)
    z_g, y_g, x_g = np.meshgrid(lin, lin, lin, indexing='ij')
    r_g = np.sqrt(z_g**2 + y_g**2 + x_g**2)
    valid = r_g <= 1.0
    basis_vol = np.zeros_like(z_g, dtype=complex)
    basis_vol[valid] = zernike_3d_basis(1, 1, 1, x_g[valid], y_g[valid], z_g[valid])
    basis_real = np.real(basis_vol)
    basis_imag = np.imag(basis_vol)
    
    # 5. Generate Unit Sphere boundary
    sphere_shell, _ = generate_unit_sphere_boundary(grid_size)
    
    # Launch Napari
    print("Launching Napari...")
    viewer = napari.Viewer(title=f"Zernike Transform Steps - Cell {cell_id}")
    
    # Step 1: Original Cell Mask
    # We display it as a label layer. 
    viewer.add_labels(submask, name='Step 1: Original Cell Mask', scale=voxel_spacing)
    
    # Scale for normalized grid layers (they go from -1 to 1). 
    # To overlay them intuitively with the cell mask, we should scale them to match the cell's physical size.
    # The cell was scaled by max_radius during moment calculation.
    z_c, y_c, x_c = np.mean(np.where(submask), axis=1) * voxel_spacing
    z_phys, y_phys, x_phys = np.where(submask)
    z_phys = z_phys * voxel_spacing[0]
    y_phys = y_phys * voxel_spacing[1]
    x_phys = x_phys * voxel_spacing[2]
    max_radius = np.max(np.sqrt((z_phys-z_c)**2 + (y_phys-y_c)**2 + (x_phys-x_c)**2))
    
    # The normalized grid goes from -1 to 1, spanning 2 units. 
    # In physical space, it spans 2 * max_radius.
    grid_scale = (2.0 * max_radius) / grid_size
    grid_scale_tuple = (grid_scale, grid_scale, grid_scale)
    
    # Calculate translation to align the center of the normalized grid to the centroid of the cell
    translation = [
        (z_c / voxel_spacing[0]) * voxel_spacing[0] - max_radius,
        (y_c / voxel_spacing[1]) * voxel_spacing[1] - max_radius,
        (x_c / voxel_spacing[2]) * voxel_spacing[2] - max_radius
    ]
    
    # Step 2: Unit Sphere
    viewer.add_image(sphere_shell.astype(float), name='Step 2: Unit Sphere Boundary', 
                     colormap='cyan', blending='additive', opacity=0.3, 
                     scale=grid_scale_tuple, translate=translation)
                     
    # Step 3: Basis Function Example
    viewer.add_image(basis_real, name='Step 3: Basis Function Z_1_1^1 (Real)', 
                     colormap='bop blue', blending='additive', opacity=0.5, visible=False,
                     scale=grid_scale_tuple, translate=translation)
                     
    viewer.add_image(basis_imag, name='Step 3: Basis Function Z_1_1^1 (Imag)', 
                     colormap='bop orange', blending='additive', opacity=0.5, visible=False,
                     scale=grid_scale_tuple, translate=translation)
                     
    # Step 4: Reconstructed Volume
    # We can display the reconstructed density as an image. Threshold it for a solid mask.
    thresh = np.max(reconstructed_vol) * 0.1
    recon_mask = (reconstructed_vol > thresh).astype(np.uint8)
    viewer.add_labels(recon_mask, name=f'Step 4: Reconstructed (N={n_max})', 
                      visible=False, opacity=0.6, scale=grid_scale_tuple, translate=translation)
                      
    # Add Moments as Text Overlay
    invariants_text = "Zernike Invariants (F_nl):\n"
    for k, v in data["invariants"].items():
        if float(v) > 0.001:
            invariants_text += f"{k}: {v:.4f}\n"
            
    viewer.text_overlay.visible = True
    viewer.text_overlay.text = invariants_text
    viewer.text_overlay.color = 'white'
    
    napari.run()

if __name__ == "__main__":
    main()
