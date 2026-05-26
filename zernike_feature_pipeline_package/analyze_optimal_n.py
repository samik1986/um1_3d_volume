import os
import json
import numpy as np
import tifffile

def main():
    target = 'crop_001_ch04'
    base_dir = r'c:\Users\banerjee\Desktop\um1_3d_volume\neuron_processing\output\custom_crops'
    tif_path = os.path.join(base_dir, f'{target}.tif')
    json_path = os.path.join(base_dir, f'{target}_intensity_zernike_gpu_n40.json')
    
    print("Loading Original Volume...")
    vol = tifffile.imread(tif_path).astype(np.float64)
    voxel_spacing = (0.5, 0.1102, 0.1102)
    dV = voxel_spacing[0] * voxel_spacing[1] * voxel_spacing[2]
    
    # Parseval's Theorem: Total Energy of the function
    # Because our integral is int f(r) * Z dV, the original energy is int |f(r)|^2 dV
    total_raw_energy = np.sum(vol**2) * dV
    print(f"Total True Biological Energy: {total_raw_energy:.4f}")
    
    print("\nLoading N=40 Zernike Spectrum...")
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    raw_moments = data['raw_moments']
    n_max = data['metadata']['n_max']
    
    # Calculate energy captured at each N
    energy_by_n = np.zeros(n_max + 1)
    
    for key, val in raw_moments.items():
        n, l, m = map(int, key.split('_'))
        C = val[0] + 1j * val[1]
        
        # Add to the energy bin for this degree N
        energy_by_n[n] += abs(C)**2
        
    cumulative_energy = np.cumsum(energy_by_n)
    energy_ratios = cumulative_energy / total_raw_energy
    
    print("\n=========================================")
    print("  Parseval Energy Recovery per Degree")
    print("=========================================")
    
    hit_90, hit_95, hit_99 = False, False, False
    
    for n in range(n_max + 1):
        ratio = energy_ratios[n] * 100
        # Print every 2nd or interesting ones
        if n % 2 == 0 or ratio > 99:
            print(f"N={n:<2} : {ratio:>6.2f}% energy captured")
            
        if ratio >= 90 and not hit_90:
            print(f">>> Reached 90% structural fidelity at N={n} <<<")
            hit_90 = True
        if ratio >= 95 and not hit_95:
            print(f">>> Reached 95% structural fidelity at N={n} <<<")
            hit_95 = True
        if ratio >= 99 and not hit_99:
            print(f">>> Reached 99% structural fidelity at N={n} <<<")
            hit_99 = True
            
    print("=========================================\n")

if __name__ == '__main__':
    main()
