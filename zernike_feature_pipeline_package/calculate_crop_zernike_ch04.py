import os
import json
import numpy as np
import tifffile
from zernike_moments import compute_zernike_moments

def main():
    crop_dir = r'c:\Users\banerjee\Desktop\um1_3d_volume\neuron_processing\output\custom_crops'
    ch04_path = os.path.join(crop_dir, 'crop_001_ch04.tif')
    
    print(f"Loading {ch04_path}...")
    ch04_vol = tifffile.imread(ch04_path)
    
    # The user requested the calculation of the entire ch04 custom_crop volume.
    # Therefore, the binary mask is all 1s (the entire bounding box volume).
    full_mask = np.ones_like(ch04_vol, dtype=np.uint8)
    
    n_max = 6
    max_functions = None
    voxel_spacing = (0.5, 0.1102, 0.1102)
    
    print(f"Computing Zernike expansion for the FULL ch04 intensity volume...")
    res = compute_zernike_moments(
        binary_mask=full_mask, 
        intensity_vol=ch04_vol,
        n_max=n_max, 
        max_functions=max_functions, 
        voxel_spacing=voxel_spacing
    )
    
    print("\n========================================")
    print("   3D Zernike Intensity Descriptors (F_{nl})")
    print("========================================")
    for key, val in res['invariants'].items():
        print(f"  F_{key[0]}_{key[1]:<4}: {val:.6f}")
    print("========================================")
    
    # Save the output
    out_dict = {
        'metadata': {
            'target': 'full_crop_001_ch04',
            'n_max': n_max,
            'max_functions': max_functions,
            'voxel_spacing_um': list(voxel_spacing),
            'volume_voxels': int(np.sum(full_mask))
        },
        'invariants': {f"F_{k[0]}_{k[1]}": float(v) for k, v in res['invariants'].items()},
        'raw_moments': {f"{k[0]}_{k[1]}_{k[2]}": [float(v.real), float(v.imag)] for k, v in res['raw_moments'].items()}
    }
    
    out_json = os.path.join(crop_dir, 'crop_001_ch04_intensity_zernike.json')
    with open(out_json, 'w') as f:
        json.dump(out_dict, f, indent=2)
        
    print(f"Structured descriptors saved to {out_json}")

if __name__ == '__main__':
    main()
