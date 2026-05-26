import json
import os

def main():
    json_path = r'c:\Users\banerjee\Desktop\um1_3d_volume\neuron_processing\output\custom_crops\crop_001_cell_2521_zernike.json'
    
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    # We can compute the sum of squared magnitudes of all coefficients 
    # either by iterating over raw_moments or invariants.
    # Since F_{nl} = sqrt( sum_m |a_{nl}^m|^2 )
    # Therefore, sum_{n,l,m} |a_{nl}^m|^2 = sum_{n,l} (F_{nl})^2
    
    sum_sq_invariants = 0.0
    for key, value in data['invariants'].items():
        sum_sq_invariants += value**2
        
    sum_sq_raw = 0.0
    for key, (real, imag) in data['raw_moments'].items():
        mag_sq = real**2 + imag**2
        sum_sq_raw += mag_sq
        
    print(f"Sum of magnitude squared of coefficients (from F_nl): {sum_sq_invariants:.6f}")
    print(f"Sum of magnitude squared of coefficients (from raw):  {sum_sq_raw:.6f}")

if __name__ == "__main__":
    main()
