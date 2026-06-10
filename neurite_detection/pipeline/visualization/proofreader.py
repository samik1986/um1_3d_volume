import os
import napari
import tifffile
import json
import numpy as np

def run_proofreader(raw_488_path, soma_mask_path=None, neurite_mask_path=None, skeleton_mask_path=None, centroids_488_path=None):
    print("\n--- Launching Napari Visualizer ---")
    viewer = napari.Viewer(ndisplay=3)
    
    print("Loading 488 Raw Volume...")
    try:
        img_488 = tifffile.memmap(raw_488_path)
    except ValueError:
        print("Image not memory-mappable, loading to RAM...")
        img_488 = tifffile.imread(raw_488_path)
    viewer.add_image(img_488, name="Raw 488", colormap="green", blending="additive", scale=(0.5, 0.1102, 0.1102))
    
    if soma_mask_path and os.path.exists(soma_mask_path):
        print("Loading 3D Soma Volume Mask...")
        soma_mask = np.load(soma_mask_path)
        viewer.add_labels(soma_mask, name="Soma Volume", scale=(0.5, 0.1102, 0.1102), opacity=0.7)
        
    if neurite_mask_path and os.path.exists(neurite_mask_path):
        print("Loading 3D Neurite Volume Mask...")
        neurite_mask = np.load(neurite_mask_path)
        # Using add_image with magenta colormap for the boolean mask for a glowing effect
        viewer.add_image(neurite_mask, name="Neurite Volume", colormap="magenta", blending="additive", scale=(0.5, 0.1102, 0.1102))
        
    if skeleton_mask_path and os.path.exists(skeleton_mask_path):
        print("Loading 3D Skeletons (Boolean Volume)...")
        skeleton_mask = np.load(skeleton_mask_path)
        viewer.add_image(skeleton_mask, name="Neurite Skeletons", colormap="cyan", blending="additive", scale=(0.5, 0.1102, 0.1102))
                
    if centroids_488_path and os.path.exists(centroids_488_path):
        c488 = np.load(centroids_488_path)
        if len(c488) > 0:
            viewer.add_points(c488, name="Cells 488 Centroids", face_color="white", size=15, blending="translucent", scale=(0.5, 0.1102, 0.1102))

    print("Viewer Ready. Close window to exit.")
    napari.run()
