import os
import json
import numpy as np
import tifffile
import joblib
from zernike_basis import zernike_3d_basis_physical

def _compute_reconstruction_component(idx, C, x_s, y_s, z_s, r_max):
    n, l, m = idx
    Z = zernike_3d_basis_physical(n, l, m, x_s, y_s, z_s, r_max)
    return C * Z

def main():
    crop_dir = r'c:\Users\banerjee\Desktop\um1_3d_volume\neuron_processing\output\custom_crops'
    tif_path = os.path.join(crop_dir, 'crop_001_ch04.tif')
    json_path = os.path.join(crop_dir, 'crop_001_ch04_intensity_zernike.json')
    out_path = os.path.join(crop_dir, 'crop_001_ch04_reconstructed.tif')
    
    print(f"Loading {tif_path}...")
    orig_vol = tifffile.imread(tif_path).astype(np.float64)
    
    print(f"Loading {json_path}...")
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    voxel_spacing = data['metadata']['voxel_spacing_um']
    raw_moments_dict = data['raw_moments']
    
    # 1. Setup Coordinates
    dz, dy, dx = voxel_spacing
    z_dim, y_dim, x_dim = orig_vol.shape
    
    z_idx, y_idx, x_idx = np.indices((z_dim, y_dim, x_dim))
    
    # The bounding sphere was calculated over all voxels in the bounding box
    # so we use all indices (since full_mask = np.ones_like)
    z_phys = z_idx.flatten() * dz
    y_phys = y_idx.flatten() * dy
    x_phys = x_idx.flatten() * dx
    
    z_c, y_c, x_c = np.mean(z_phys), np.mean(y_phys), np.mean(x_phys)
    z_shifted = z_phys - z_c
    y_shifted = y_phys - y_c
    x_shifted = x_phys - x_c
    
    max_radius = np.max(np.sqrt(z_shifted**2 + y_shifted**2 + x_shifted**2))
    print(f"Bounding Radius: {max_radius:.4f} um")
    
    # 2. Parse Coefficients
    coeffs = {}
    for key, val in raw_moments_dict.items():
        n, l, m = map(int, key.split('_'))
        C = val[0] + 1j * val[1]
        coeffs[(n, l, m)] = C
        
    # 3. Reconstruct
    print(f"Reconstructing volume from {len(coeffs)} basis functions...")
    
    import os as pyos
    num_workers = pyos.cpu_count() or 4
    
    # Run evaluation in parallel
    components = joblib.Parallel(n_jobs=num_workers)(
        joblib.delayed(_compute_reconstruction_component)(
            idx, C, x_shifted, y_shifted, z_shifted, max_radius
        ) 
        for idx, C in coeffs.items()
    )
    
    print("Summing components...")
    f_v_complex = np.sum(components, axis=0)
    
    max_imag = np.max(np.abs(f_v_complex.imag))
    print(f"Maximum imaginary part (should be ~0): {max_imag:.4e}")
    
    recon_flat = f_v_complex.real
    recon_vol = recon_flat.reshape((z_dim, y_dim, x_dim))
    
    # 4. Compare Side-by-Side
    # Calculate MSE and Correlation
    mse = np.mean((orig_vol - recon_vol)**2)
    
    # Pearson Correlation Coefficient
    orig_flat = orig_vol.flatten()
    r = np.corrcoef(orig_flat, recon_flat)[0, 1]
    
    # Parseval's theorem equivalent for actual signals
    orig_energy = np.sum(orig_flat**2)
    recon_energy = np.sum(recon_flat**2)
    
    print("\n========================================")
    print("        Reconstruction Metrics")
    print("========================================")
    print(f"Original Volume Energy : {orig_energy:.2f}")
    print(f"Reconstructed Energy   : {recon_energy:.2f}")
    print(f"Mean Squared Error     : {mse:.4f}")
    print(f"Pearson Correlation    : {r:.4f}")
    print("========================================\n")
    
    # Save the reconstructed volume (normalized for viewing)
    recon_vol_uint16 = np.clip(recon_vol, 0, 65535).astype(np.uint16)
    tifffile.imwrite(out_path, recon_vol_uint16)
    print(f"Reconstructed volume saved to: {out_path}")

if __name__ == '__main__':
    main()
