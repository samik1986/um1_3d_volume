import tifffile
import numpy as np

mask = tifffile.imread(r"c:\Users\banerjee\Desktop\Current Work\um1_3d_volume\NEWFP_output\F0046_multichannel_cmle_ch03\skeleton_mask.tif")
z_idx, y_idx, x_idx = np.where(mask > 0)
print(f"Mask Voxel Bounding Box:")
print(f"Z: {z_idx.min()} to {z_idx.max()}")
print(f"Y: {y_idx.min()} to {y_idx.max()}")
print(f"X: {x_idx.min()} to {x_idx.max()}")

print(f"Mask Physical Bounding Box (Z*0.5, Y*0.1102, X*0.1102):")
print(f"Z: {z_idx.min()*0.5} to {z_idx.max()*0.5}")
print(f"Y: {y_idx.min()*0.1102} to {y_idx.max()*0.1102}")
print(f"X: {x_idx.min()*0.1102} to {x_idx.max()*0.1102}")

swc_file = r"c:\Users\banerjee\Desktop\Current Work\um1_3d_volume\NEWFP_output\F0046_multichannel_cmle_ch03\skeletons_smooth.swc"
xs, ys, zs = [], [], []
with open(swc_file, 'r') as f:
    for line in f:
        if line.startswith('#') or not line.strip(): continue
        parts = line.strip().split()
        if len(parts) >= 7:
            xs.append(float(parts[2]))
            ys.append(float(parts[3]))
            zs.append(float(parts[4]))

print(f"SWC Bounding Box:")
print(f"Z: {min(zs)} to {max(zs)}")
print(f"Y: {min(ys)} to {max(ys)}")
print(f"X: {min(xs)} to {max(xs)}")
