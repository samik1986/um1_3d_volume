import os
import numpy as np
import tifffile

def main():
    crop_dir = r'c:\Users\banerjee\Desktop\um1_3d_volume\neuron_processing\output\custom_crops'
    ch04_path = os.path.join(crop_dir, 'crop_001_ch04.tif')
    labels_path = os.path.join(crop_dir, 'crop_001_labels.tif')
    
    print(f"Loading {ch04_path}...")
    ch04_vol = tifffile.imread(ch04_path)
    
    # Calculate sum of squares for the entire crop volume
    sum_sq_total = np.sum(ch04_vol.astype(np.float64)**2)
    print(f"Sum of squares of all voxel values in the entire crop: {sum_sq_total}")
    
    # Also calculate inside the specific cell 2521 (in case you meant inside the cell boundary)
    if os.path.exists(labels_path):
        labels_vol = tifffile.imread(labels_path)
        cell_mask = labels_vol == 2521
        sum_sq_cell = np.sum(ch04_vol[cell_mask].astype(np.float64)**2)
        print(f"Sum of squares of voxel values inside cell 2521 only: {sum_sq_cell}")

if __name__ == '__main__':
    main()
