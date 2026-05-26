import os
import json
import numpy as np
import tifffile
from show_custom_crop import find_spherical_cell
from zernike_moments import compute_zernike_moments

def main():
    crop_dir = r'c:\Users\banerjee\Desktop\um1_3d_volume\neuron_processing\output\custom_crops'
    labels_path = os.path.join(crop_dir, 'crop_001_labels.tif')
    
    if not os.path.exists(labels_path):
        print(f"Error: Could not find crop labels at {labels_path}")
        return
        
    print(f"Loading {labels_path}...")
    labels_vol = tifffile.imread(labels_path)
    
    print("Finding the most spherical central cell...")
    cell_id, score = find_spherical_cell(labels_vol)
    
    if cell_id is None:
        print("No suitable cell found.")
        return
        
    print(f"Target cell ID: {cell_id} (Score: {score:.3f})")
    
    # Isolate the cell mask
    mask = (labels_vol == cell_id).astype(np.uint8)
    
    # Voxel physical dimensions from previous context
    # dz=0.5, dy=0.1102, dx=0.1102
    voxel_spacing = (0.5, 0.1102, 0.1102)
    n_max = 10
    
    print(f"Computing 3D Zernike Moments up to degree N={n_max}...")
    print(f"Voxel spacing: {voxel_spacing} um")
    
    results = compute_zernike_moments(mask, n_max=n_max, max_functions=36, voxel_spacing=voxel_spacing)
    invariants = results['invariants']
    
    print("\n" + "="*40)
    print("   3D Zernike Shape Descriptors (F_{nl})")
    print("="*40)
    
    invariants_dict = {}
    raw_moments_dict = {}
    
    for n in range(n_max + 1):
        for l in range(n + 1):
            if (n - l) % 2 == 0:
                if (n, l) not in invariants:
                    continue
                val = invariants[(n, l)]
                key = f"F_{n}_{l}"
                invariants_dict[key] = float(val)
                print(f"  {key:8} : {val:.6f}")
                
                # Also save raw moments for this n,l pair
                for m in range(-l, l + 1):
                    if (n, l, m) not in results['raw_moments']:
                        continue
                    raw_val = results['raw_moments'][(n, l, m)]
                    raw_key = f"{n}_{l}_{m}"
                    raw_moments_dict[raw_key] = [float(np.real(raw_val)), float(np.imag(raw_val))]
                
    # Prepare metadata
    volume_voxels = int(np.sum(mask))
    
    out_data = {
        "metadata": {
            "cell_id": int(cell_id),
            "n_max": n_max,
            "voxel_spacing_um": list(voxel_spacing),
            "volume_voxels": volume_voxels
        },
        "invariants": invariants_dict,
        "raw_moments": raw_moments_dict
    }
                
    # Save descriptors to JSON
    out_json = os.path.join(crop_dir, f'crop_001_cell_{cell_id}_zernike.json')
    with open(out_json, 'w') as f:
        json.dump(out_data, f, indent=2)
        
    print("="*40)
    print(f"Structured descriptors saved to {out_json}")

if __name__ == "__main__":
    main()
