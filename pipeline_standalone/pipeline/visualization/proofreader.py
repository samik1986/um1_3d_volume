"""
proofreader.py (neurite_detection/pipeline/visualization)

Author: Samik Banerjee
Date: June 10, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

Interactive Napari proofreader for correcting network topologies with intensity snapping.
"""

import os
import napari
import tifffile
import json
import numpy as np

def run_proofreader(raw_488_path, soma_mask_path=None, neurite_mask_path=None, skeleton_mask_path=None, centroids_488_path=None, barcodes_555_path=None, barcodes_640_path=None, disc_soma_path=None, disc_neurite_path=None, disc_skel_path=None, disc_555_path=None, disc_640_path=None, skeleton_json_path=None):
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
        soma_mask = np.load(soma_mask_path, mmap_mode='r')
        viewer.add_labels(soma_mask, name="Soma Volume", scale=(0.5, 0.1102, 0.1102), opacity=0.7)
        
    if neurite_mask_path and os.path.exists(neurite_mask_path):
        print("Loading 3D Neurite Volume Mask...")
        neurite_mask = np.load(neurite_mask_path, mmap_mode='r')
        # Using add_image with magenta colormap for the boolean mask for a glowing effect
        viewer.add_image(neurite_mask, name="Neurite Volume", colormap="magenta", blending="additive", scale=(0.5, 0.1102, 0.1102))
        
    if skeleton_mask_path and os.path.exists(skeleton_mask_path):
        print("Loading 3D Skeletons (Boolean Volume)...")
        skeleton_mask = np.load(skeleton_mask_path, mmap_mode='r')
        viewer.add_image(skeleton_mask, name="Neurite Skeletons", colormap="cyan", blending="additive", scale=(0.5, 0.1102, 0.1102))
        
    if skeleton_json_path and os.path.exists(skeleton_json_path):
        print("Loading 3D Skeletons from JSON...")
        with open(skeleton_json_path, 'r') as f:
            data = json.load(f)
        paths = []
        for line in data.get("cells_1_linestrings", []):
            paths.append(line["geometry"])
        if len(paths) > 0:
            viewer.add_shapes(paths, shape_type='path', edge_color='cyan', name="JSON Skeletons", scale=(0.5, 0.1102, 0.1102), edge_width=1)
                
    if centroids_488_path and os.path.exists(centroids_488_path):
        c488 = np.load(centroids_488_path)
        if len(c488) > 0:
            viewer.add_points(c488, name="Cells 488 Centroids", face_color="white", size=15, blending="translucent", scale=(0.5, 0.1102, 0.1102))
            
    if barcodes_555_path and os.path.exists(barcodes_555_path):
        b555 = np.load(barcodes_555_path)
        if len(b555) > 0:
            viewer.add_points(b555, name="Filtered Barcodes 555", face_color="yellow", size=10, blending="translucent", scale=(0.5, 0.1102, 0.1102))

    if barcodes_640_path and os.path.exists(barcodes_640_path):
        b640 = np.load(barcodes_640_path)
        if len(b640) > 0:
            viewer.add_points(b640, name="Filtered Barcodes 640", face_color="red", size=10, blending="translucent", scale=(0.5, 0.1102, 0.1102))

    if disc_soma_path and os.path.exists(disc_soma_path):
        d_soma = np.load(disc_soma_path, mmap_mode='r')
        viewer.add_labels(d_soma, name="Discarded Soma", scale=(0.5, 0.1102, 0.1102), opacity=0.3)
        
    if disc_neurite_path and os.path.exists(disc_neurite_path):
        d_neur = np.load(disc_neurite_path, mmap_mode='r')
        viewer.add_image(d_neur, name="Discarded Neurites", colormap="gray", blending="additive", scale=(0.5, 0.1102, 0.1102), opacity=0.3)

    if disc_skel_path and os.path.exists(disc_skel_path):
        d_skel = np.load(disc_skel_path, mmap_mode='r')
        viewer.add_image(d_skel, name="Discarded Skeletons", colormap="blue", blending="additive", scale=(0.5, 0.1102, 0.1102), opacity=0.3)

    if disc_555_path and os.path.exists(disc_555_path):
        d555 = np.load(disc_555_path)
        if len(d555) > 0:
            viewer.add_points(d555, name="Discarded 555", face_color="orange", size=10, blending="translucent", scale=(0.5, 0.1102, 0.1102))

    if disc_640_path and os.path.exists(disc_640_path):
        d640 = np.load(disc_640_path)
        if len(d640) > 0:
            viewer.add_points(d640, name="Discarded 640", face_color="pink", size=10, blending="translucent", scale=(0.5, 0.1102, 0.1102))

    print("Viewer Ready. Close window to exit.")
    napari.run()
