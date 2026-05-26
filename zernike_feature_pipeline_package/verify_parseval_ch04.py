import os
import json
import numpy as np
import tifffile

def main():
    crop_dir = r'c:\Users\banerjee\Desktop\um1_3d_volume\neuron_processing\output\custom_crops'
    json_path = os.path.join(crop_dir, 'crop_001_ch04_intensity_zernike.json')
    tif_path = os.path.join(crop_dir, 'crop_001_ch04.tif')
    
    # 1. Parseval sum from coefficients
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    sum_sq_coeffs = 0.0
    for key, value in data['invariants'].items():
        sum_sq_coeffs += value**2
        
    # 2. Integral of squared intensity over the volume
    ch04_vol = tifffile.imread(tif_path).astype(np.float64)
    
    dz, dy, dx = 0.5, 0.1102, 0.1102
    dV = dz * dy * dx
    
    # Integral = sum( I^2 ) * dV
    sum_sq_intensity = np.sum(ch04_vol**2) * dV
    
    print("========================================")
    print("      PARSEVAL'S ENERGY VERIFICATION    ")
    print("========================================")
    print(f"Energy in Zernike Expansion (N=10) : {sum_sq_coeffs:.6f}")
    print(f"Total True Signal Energy (I^2 * dV): {sum_sq_intensity:.6f}")
    print("----------------------------------------")
    percent_captured = (sum_sq_coeffs / sum_sq_intensity) * 100
    print(f"Energy Captured by N=10 Polynomials: {percent_captured:.2f} %")
    print("========================================")

if __name__ == '__main__':
    main()
