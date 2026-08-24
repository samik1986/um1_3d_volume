import os
import sys
import napari
import tifffile
import json
import numpy as np

def load_downsampled_tiff(path, stride=4):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return None
    vol = tifffile.imread(path)
    sub = vol[::stride, ::stride, ::stride].copy()
    del vol
    return sub

def main():
    input_dir = r"c:\Users\banerjee\Desktop\um1_3d_volume"
    raw_488_path = os.path.join(input_dir, "B3Well7_1_AN_20260529_233255_Area1_round0_20260529_233740_488_F0044_cmle.tif")
    
    stride = 4
    scale = (0.5 * stride, 0.1102 * stride, 0.1102 * stride)
    
    print("Loading downsampled volume for parameter tuning...")
    raw_488 = load_downsampled_tiff(raw_488_path, stride)
    
    viewer = napari.Viewer(ndisplay=3)
    
    layer = None
    if raw_488 is not None:
        layer = viewer.add_image(raw_488, name="Raw 488", colormap="green", blending="additive", scale=scale)
    
    print("\n" + "="*60)
    print("INSTRUCTIONS:")
    print("1. Adjust the contrast limits and gamma slider in the left panel for the 'Raw 488' layer.")
    print("2. When you are satisfied with the look, close the Napari window.")
    print("3. The final parameters will be saved for the neurite detection pipeline.")
    print("="*60 + "\n")
    
    napari.run()
    
    if layer is not None:
        gamma = layer.gamma
        contrast_limits = layer.contrast_limits
        print("\nCaptured Parameters:")
        print(f"Gamma: {gamma}")
        print(f"Contrast Limits: {contrast_limits}")
        
        # Save to a json file
        params = {
            "gamma": gamma,
            "contrast_limits": contrast_limits
        }
        
        config_path = "pipeline_parameters.json"
        with open(config_path, "w") as f:
            json.dump(params, f, indent=4)
        
        print(f"Parameters saved to {config_path}")

if __name__ == "__main__":
    main()
