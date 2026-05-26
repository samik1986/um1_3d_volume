import os
import json
import numpy as np

def main():
    target = 'crop_001_ch04'
    base_dir = r'c:\Users\banerjee\Desktop\um1_3d_volume\neuron_processing\output\custom_crops'
    json_path = os.path.join(base_dir, f'{target}_intensity_zernike_gpu_n20.json')
    out_path = os.path.join(base_dir, 'optimal_basis_keys.json')
    
    print(f"Loading {json_path}...")
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    invariants = data['invariants']
    
    # Calculate energy per (n, l) shell
    # F_nl in the json is the square root of the energy, so energy = F_nl**2
    shell_energies = {}
    for key, f_val in invariants.items():
        # key is "F_n_l"
        parts = key.split('_')
        n = int(parts[1])
        l = int(parts[2])
        shell_energies[(n, l)] = f_val**2
        
    total_zernike_energy = sum(shell_energies.values())
    print(f"Total Zernike Energy (N=20): {total_zernike_energy:.4f}")
    
    # Sort shells by descending energy
    sorted_shells = sorted(shell_energies.items(), key=lambda item: item[1], reverse=True)
    
    cumulative_energy = 0.0
    selected_shells = []
    target_ratio = 0.99
    
    print(f"\nSelecting top (n, l) shells to capture {target_ratio * 100}% of Zernike energy...")
    
    for (n, l), energy in sorted_shells:
        selected_shells.append([n, l])
        cumulative_energy += energy
        
        if cumulative_energy / total_zernike_energy >= target_ratio:
            break
            
    num_selected_shells = len(selected_shells)
    total_shells = len(sorted_shells)
    
    # Calculate total basis functions
    num_functions = sum(2 * l + 1 for n, l in selected_shells)
    total_functions = sum(2 * l + 1 for (n, l), _ in sorted_shells)
    
    print("\n=========================================")
    print("  Dimensionality Reduction Results")
    print("=========================================")
    print(f"Original (n, l) shells: {total_shells}")
    print(f"Selected (n, l) shells: {num_selected_shells}")
    print(f"Dropped shells: {total_shells - num_selected_shells}")
    print("---")
    print(f"Original basis functions: {total_functions}")
    print(f"Selected basis functions: {num_functions}")
    print(f"Dropped basis functions: {total_functions - num_functions}")
    print(f"Memory reduction: {100 * (1 - num_functions / total_functions):.2f}%")
    print("=========================================\n")
    
    # Save the selected shells
    output_data = {
        "target_ratio": target_ratio,
        "selected_shells_n_l": selected_shells,
        "num_functions": num_functions
    }
    
    with open(out_path, 'w') as f:
        json.dump(output_data, f, indent=2)
        
    print(f"Optimal keys saved to {out_path}")

if __name__ == '__main__':
    main()
