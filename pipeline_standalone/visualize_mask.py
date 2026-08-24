import argparse
import tifffile
import os

def visualize_mask(raw_volume_path, mask_path):
    print("Launching Napari for visualization...")
    import napari
        
    viewer = napari.Viewer(ndisplay=3)
    
    # Load raw volume
    if os.path.exists(raw_volume_path):
        print(f"Loading raw volume: {raw_volume_path}")
        raw_volume = tifffile.imread(raw_volume_path)
        viewer.add_image(raw_volume, name='Raw Volume', colormap='gray', blending='additive', scale=(0.5, 0.1102, 0.1102))
    
    # Load mask
    if os.path.exists(mask_path):
        print(f"Loading mask: {mask_path}")
        mask = tifffile.imread(mask_path)
        viewer.add_image(mask, name='Skeleton Mask', colormap='red', blending='additive', scale=(0.5, 0.1102, 0.1102))
        
    napari.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--volume', required=True)
    parser.add_argument('--mask', required=True)
    args = parser.parse_args()
    visualize_mask(args.volume, args.mask)
