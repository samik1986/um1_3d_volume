import os
import tifffile
import numpy as np

def create_crop():
    input_path = r"C:\Users\banerjee\Desktop\um1_3d_volume\B3Well7_1_AN_20260529_233255_Area1_round0_20260529_233740_488_F0044_cmle.tif"
    output_dir = "tutorial_data"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "tutorial_crop.tif")

    print(f"Loading {input_path}...")
    img = tifffile.imread(input_path)
    
    # img shape is likely (Z, Y, X)
    Z, Y, X = img.shape
    
    # Crop size
    cz, cy, cx = 32, 256, 256
    
    # Ensure crop size is not larger than image
    cz = min(cz, Z)
    cy = min(cy, Y)
    cx = min(cx, X)
    
    # Center coordinates
    z0 = Z // 2 - cz // 2
    y0 = Y // 2 - cy // 2
    x0 = X // 2 - cx // 2
    
    print(f"Cropping region Z:{z0}-{z0+cz}, Y:{y0}-{y0+cy}, X:{x0}-{x0+cx}...")
    crop = img[z0:z0+cz, y0:y0+cy, x0:x0+cx]
    
    tifffile.imwrite(output_path, crop)
    print(f"Saved crop to {output_path}")

if __name__ == "__main__":
    create_crop()
