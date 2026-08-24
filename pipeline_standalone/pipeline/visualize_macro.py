import os
import napari
import numpy as np
import tifffile

def load_downsampled(path, stride=4):
    if not os.path.exists(path):
        return None
    vol = np.load(path, mmap_mode='r')
    return np.array(vol[::stride, ::stride, ::stride])

def load_downsampled_tiff(path, stride=4):
    if not os.path.exists(path):
        return None
    vol = tifffile.imread(path)
    sub = vol[::stride, ::stride, ::stride].copy()
    del vol
    return sub

def main():
    input_dir = r"c:\Users\banerjee\Desktop\um1_3d_volume"
    output_dir = r"c:\Users\banerjee\Desktop\um1_3d_volume\neurite_detection\pipeline_output"
    prefix = "B3Well7_1_AN_20260529_233255_Area1_round0_20260529_233740_488_F0044_cmle_"
    raw_488_path = os.path.join(input_dir, "B3Well7_1_AN_20260529_233255_Area1_round0_20260529_233740_488_F0044_cmle.tif")
    
    stride = 4
    # We maintain the physical aspect ratio (0.5, 0.1102, 0.1102)
    # but scale it up by the stride so the 3D geometry looks identical
    scale = (0.5 * stride, 0.1102 * stride, 0.1102 * stride)
    
    print(f"Loading Macro View (Downsampled {stride}x)...")
    print("\n" + "="*50)
    print("HOW TO FIND YOUR COORDINATES:")
    print(f"Napari will show the layer indices (e.g. [z, y, x]).")
    print(f"Because this volume is shrunk by {stride}x, you must MULTIPLY the layer indices by {stride}")
    print("to get the real coordinates for the visualizer!")
    print("Example: If you hover over a cell and Napari shows [20, 250, 300],")
    print(f"the real coordinates are: Z=80, Y=1000, X=1200")
    print("="*50 + "\n")
    
    raw_488 = load_downsampled_tiff(raw_488_path, stride)
    neurites = load_downsampled(os.path.join(output_dir, f"{prefix}neurite_mask_488.npy"), stride)
    skeletons = load_downsampled(os.path.join(output_dir, f"{prefix}skeleton_mask_488.npy"), stride)
    somas = load_downsampled(os.path.join(output_dir, f"{prefix}soma_mask_488.npy"), stride)
    
    viewer = napari.Viewer(ndisplay=3)
    
    if raw_488 is not None:
        viewer.add_image(raw_488, name="Raw 488", colormap="green", blending="additive", scale=scale)
    if somas is not None:
        viewer.add_labels(somas, name="Soma Mask", scale=scale)
    if neurites is not None:
        viewer.add_image(neurites, name="Neurites", colormap="magenta", blending="additive", scale=scale, opacity=0.5)
    if skeletons is not None:
        viewer.add_image(skeletons, name="Skeletons", colormap="cyan", blending="additive", scale=scale, opacity=0.8)

    print("Macro Viewer Ready. Close window to exit.")
    napari.run()

if __name__ == "__main__":
    main()
