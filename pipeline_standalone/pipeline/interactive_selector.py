import os
import sys
import napari
import numpy as np
import tifffile

def load_downsampled(path, stride=4):
    if not os.path.exists(path): return None
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
    scale = (0.5 * stride, 0.1102 * stride, 0.1102 * stride)
    
    print("Loading downsampled volume for visual selection...")
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
        skel_pts = np.argwhere(skeletons)
        if len(skel_pts) > 0:
            viewer.add_points(skel_pts, name="Skeletons", face_color="cyan", size=3, scale=scale)

    shapes_layer = viewer.add_shapes(
        name="DRAW BOUNDING BOX HERE",
        shape_type='rectangle',
        edge_width=5,
        edge_color='yellow',
        face_color='transparent',
        scale=scale,
        ndim=3
    )
    
    print("\n" + "="*60)
    print("INSTRUCTIONS:")
    print("1. Click the '2D/3D' button (cube icon at bottom left) to switch to 2D view.")
    print("2. Select the 'DRAW BOUNDING BOX HERE' layer on the left.")
    print("3. Click the 'Add Rectangle' tool (square icon) at the top left.")
    print("4. Draw a rectangle over the region you want to select.")
    print("5. Close the Napari window when you are done.")
    print("="*60 + "\n")
    
    napari.run()
    
    if len(shapes_layer.data) > 0:
        rect = shapes_layer.data[0] # (4, 3)
        y_min = int(np.min(rect[:, 1]) * stride)
        y_max = int(np.max(rect[:, 1]) * stride)
        x_min = int(np.min(rect[:, 2]) * stride)
        x_max = int(np.max(rect[:, 2]) * stride)
        
        y_min = max(0, y_min)
        y_max = min(2720, y_max)
        x_min = max(0, x_min)
        x_max = min(2720, x_max)
        
        print(f"\nUser selected bounding box: Y=[{y_min}:{y_max}], X=[{x_min}:{x_max}]")
        print("Launching full-resolution visualizer for this subvolume...")
        
        sys.argv = ["visualize_subvolume.py", "--y_start", str(y_min), "--y_end", str(y_max), "--x_start", str(x_min), "--x_end", str(x_max)]
        import visualize_subvolume
        visualize_subvolume.main()
    else:
        print("\nNo bounding box was drawn. Exiting.")

if __name__ == "__main__":
    main()
