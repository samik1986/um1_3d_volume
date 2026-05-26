import os
import numpy as np
import tifffile

def main():
    crop_dir = r'c:\Users\banerjee\Desktop\um1_3d_volume\neuron_processing\output\custom_crops'
    ch04_path = os.path.join(crop_dir, 'crop_001_ch04.tif')
    labels_path = os.path.join(crop_dir, 'crop_001_labels.tif')
    
    # Physical dimensions of a voxel
    dz, dy, dx = 0.5, 0.1102, 0.1102
    voxel_volume_um3 = dz * dy * dx
    
    print(f"Loading {ch04_path}...")
    ch04_vol = tifffile.imread(ch04_path)
    
    # Calculate the integral of the intensity values for the entire crop
    sum_total = np.sum(ch04_vol.astype(np.float64))
    integral_total = sum_total * voxel_volume_um3
    
    print(f"Voxel volume: {voxel_volume_um3:.6f} um^3")
    print(f"Integral of voxel intensities in the entire crop: {integral_total:.2f}")
    
    # Calculate inside the specific cell 2521
    if os.path.exists(labels_path):
        labels_vol = tifffile.imread(labels_path)
        cell_mask = labels_vol == 2521
        sum_cell = np.sum(ch04_vol[cell_mask].astype(np.float64))
        integral_cell = sum_cell * voxel_volume_um3
        print(f"Integral of voxel intensities inside cell 2521 only: {integral_cell:.2f}")

if __name__ == '__main__':
    main()
