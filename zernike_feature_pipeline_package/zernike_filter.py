import os
import json
import argparse
import numpy as np
import tifffile
import joblib
from zernike_basis import zernike_3d_basis_physical

def _compute_reconstruction_component(idx, C, x_s, y_s, z_s, r_max):
    n, l, m = idx
    Z = zernike_3d_basis_physical(n, l, m, x_s, y_s, z_s, r_max)
    return C * Z

def main():
    parser = argparse.ArgumentParser(description="Apply spatial filter using Zernike basis functions.")
    parser.add_argument('--tif', type=str, required=True, help="Path to original .tif volume")
    parser.add_argument('--json', type=str, required=True, help="Path to the extracted Zernike .json coefficients")
    parser.add_argument('--n-min', type=int, default=0, help="Minimum Zernike degree (n) to include in reconstruction")
    parser.add_argument('--n-max', type=int, default=1000, help="Maximum Zernike degree (n) to include in reconstruction")
    parser.add_argument('--out', type=str, default=None, help="Path to save the filtered .tif volume")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.tif):
        print(f"Error: Original TIF file {args.tif} not found.")
        return
        
    if not os.path.exists(args.json):
        print(f"Error: JSON file {args.json} not found.")
        return
        
    if args.out is None:
        base, ext = os.path.splitext(args.tif)
        args.out = f"{base}_filtered_nmin{args.n_min}_nmax{args.n_max}{ext}"
    
    print(f"Loading {args.tif}...")
    orig_vol = tifffile.imread(args.tif).astype(np.float64)
    
    print(f"Loading {args.json}...")
    with open(args.json, 'r') as f:
        data = json.load(f)
        
    voxel_spacing = data['metadata']['voxel_spacing_um']
    raw_moments_dict = data['raw_moments']
    
    # 1. Setup Coordinates
    dz, dy, dx = voxel_spacing
    z_dim, y_dim, x_dim = orig_vol.shape
    
    z_idx, y_idx, x_idx = np.indices((z_dim, y_dim, x_dim))
    
    z_phys = z_idx.flatten() * dz
    y_phys = y_idx.flatten() * dy
    x_phys = x_idx.flatten() * dx
    
    z_c, y_c, x_c = np.mean(z_phys), np.mean(y_phys), np.mean(x_phys)
    z_shifted = z_phys - z_c
    y_shifted = y_phys - y_c
    x_shifted = x_phys - x_c
    
    max_radius = np.max(np.sqrt(z_shifted**2 + y_shifted**2 + x_shifted**2))
    
    # 2. Parse and Filter Coefficients
    filtered_coeffs = {}
    total_coeffs = 0
    for key, val in raw_moments_dict.items():
        n, l, m = map(int, key.split('_'))
        total_coeffs += 1
        
        # Apply Frequency Filter
        if args.n_min <= n <= args.n_max:
            C = val[0] + 1j * val[1]
            filtered_coeffs[(n, l, m)] = C
            
    print(f"Filter active: N in [{args.n_min}, {args.n_max}]")
    print(f"Retained {len(filtered_coeffs)} out of {total_coeffs} basis functions.")
    
    if len(filtered_coeffs) == 0:
        print("Warning: The filter excluded all coefficients! Output will be zero.")
        recon_vol = np.zeros_like(orig_vol)
        recon_flat = recon_vol.flatten()
    else:
        # 3. Reconstruct
        print(f"Reconstructing filtered volume...")
        
        import os as pyos
        num_workers = pyos.cpu_count() or 4
        
        components = joblib.Parallel(n_jobs=num_workers)(
            joblib.delayed(_compute_reconstruction_component)(
                idx, C, x_shifted, y_shifted, z_shifted, max_radius
            ) 
            for idx, C in filtered_coeffs.items()
        )
        
        print("Summing components...")
        f_v_complex = np.sum(components, axis=0)
        
        max_imag = np.max(np.abs(f_v_complex.imag))
        print(f"Maximum imaginary part (should be ~0): {max_imag:.4e}")
        
        recon_flat = f_v_complex.real
        recon_vol = recon_flat.reshape((z_dim, y_dim, x_dim))
    
    # 4. Compare Side-by-Side
    mse = np.mean((orig_vol - recon_vol)**2)
    
    orig_flat = orig_vol.flatten()
    r = np.corrcoef(orig_flat, recon_flat)[0, 1] if len(filtered_coeffs) > 0 else 0.0
    
    orig_energy = np.sum(orig_flat**2)
    recon_energy = np.sum(recon_flat**2)
    
    print("\n========================================")
    print("        Filter Metrics")
    print("========================================")
    print(f"Original Volume Energy : {orig_energy:.2f}")
    print(f"Filtered Energy        : {recon_energy:.2f}")
    if orig_energy > 0:
        print(f"Energy Retained        : {(recon_energy/orig_energy)*100:.2f}%")
    print(f"Mean Squared Error     : {mse:.4f}")
    print(f"Pearson Correlation    : {r:.4f}")
    print("========================================\n")
    
    # Save the reconstructed volume
    # To handle negative values or floating points from band-pass, 
    # we shift/scale to standard 16-bit visualization
    recon_vol_uint16 = np.clip(recon_vol, 0, 65535).astype(np.uint16)
    tifffile.imwrite(args.out, recon_vol_uint16)
    print(f"Filtered volume saved to: {args.out}")

if __name__ == '__main__':
    main()
