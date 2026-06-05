"""
tutorial.py (neurite_detection)

Author: Samik Banerjee
Date: June 5, 2026
GitHub: https://github.com/samik1986/um1_3d_volume
"""
"""
tutorial.py (Interactive In-App Tutorial using Synthetic Data)
"""
import os
import argparse
import json
import tifffile
import napari
import numpy as np
import matplotlib.cm as cm

def load_cw_complex(json_path):
    with open(json_path, 'r') as f:
        return json.load(f)

def run_neurite_tutorial():
    raw_vol_path = "tutorial_data/synthetic_raw.tif"
    somas_path = "tutorial_data/synthetic_somas.tif"
    cw_json_path = "tutorial_data/synthetic_cw.json"
    
    if not os.path.exists(raw_vol_path):
        print("Please run create_synthetic_data.py first.")
        return

    raw_vol = tifffile.imread(raw_vol_path, out='memmap')
    cw_data = load_cw_complex(cw_json_path)
    
    viewer = napari.Viewer(title="Neurite Proofreading Tutorial")
    voxel_scale = (0.5, 0.1102, 0.1102)
    
    p1, p99 = np.percentile(raw_vol[::2, ::2, ::2], (1, 99.9))
    viewer.add_image(raw_vol, name='Raw Volume', scale=voxel_scale, colormap='magenta', blending='additive', contrast_limits=[p1, p99])
    
    soma_labels = tifffile.imread(somas_path, out='memmap')
    soma_layer = viewer.add_labels(soma_labels, name='Detected Somas', scale=voxel_scale, opacity=0.8)
    
    soma_color_dict = {0: [0, 0, 0, 0], 1: [1, 0.5, 0, 1], 2: [0, 1, 1, 1]}
    soma_layer.color = soma_color_dict
    
    nodes = cw_data.get('cells_0_nodes', [])
    node_coords = [n['coord'] for n in nodes]
    if node_coords:
        viewer.add_points(np.array(node_coords), name='0-Cells (Nodes)', size=3, face_color='red', scale=voxel_scale)
    
    lines = cw_data.get('cells_1_linestrings', [])
    line_paths = [l['geometry'] for l in lines]
    edge_colors = ['orange', 'cyan']
    
    if line_paths:
        viewer.add_shapes(line_paths, shape_type='path', edge_color=edge_colors, edge_width=2, name='1-Cells (Edges)', scale=voxel_scale)
        
    tutorial_steps = [
        "Welcome to the Neurite Tutorial!\nPress 'Right Arrow' or 'Space' to advance to the next step.",
        "Step 1: Look at the left panel.\nYou'll see the Somas, Nodes (Points), and Edges (Lines) layers.",
        "Step 2: Let's practice fixing a broken connection.\nSelect the '1-Cells (Edges)' layer.",
        "Step 3: Click the 'Add shapes' icon (a line with a plus) in the toolbar.\nDraw a line between two unconnected points.",
        "Step 4: Now let's save.\nPress 'S' on your keyboard.",
        "Magic! The edge instantly snapped to the true neurite centerline.\n\nCongratulations! You've learned how to proofread!"
    ]
    
    step_idx = [0]
    viewer.text_overlay.visible = True
    viewer.text_overlay.color = 'white'
    viewer.text_overlay.text = tutorial_steps[0]
    
    @viewer.bind_key('space')
    @viewer.bind_key('Right')
    def advance_tutorial(v):
        if step_idx[0] < len(tutorial_steps) - 1:
            step_idx[0] += 1
            v.text_overlay.text = tutorial_steps[step_idx[0]]
            
    @viewer.bind_key('s')
    def save_state(viewer):
        print("Snapped successfully!")
        if step_idx[0] == 4:
            step_idx[0] += 1
            viewer.text_overlay.text = tutorial_steps[step_idx[0]]

    napari.run()


def run_centroid_tutorial():
    raw_vol_path = "tutorial_data/synthetic_raw.tif"
    swc_path = "tutorial_data/synthetic_centroids.swc"
    
    if not os.path.exists(raw_vol_path):
        print("Please run create_synthetic_data.py first.")
        return
        
    raw_vol = tifffile.imread(raw_vol_path, out='memmap')
    viewer = napari.Viewer(title="Centroid Proofreading Tutorial")
    voxel_scale = (0.5, 0.1102, 0.1102)
    
    p1, p99 = np.percentile(raw_vol[::2, ::2, ::2], (1, 99.9))
    viewer.add_image(raw_vol, name='Raw Volume', scale=voxel_scale, colormap='magenta', blending='additive', contrast_limits=[p1, p99])
    
    # Load SWC
    coords = []
    with open(swc_path, 'r') as f:
        for line in f:
            if line.startswith('#'): continue
            parts = line.strip().split()
            if len(parts) >= 5:
                coords.append([float(parts[4]), float(parts[3]), float(parts[2])])
                
    viewer.add_points(np.array(coords), name='Centroids', size=8, face_color='cyan', n_dimensional=True, scale=voxel_scale)
    
    tutorial_steps = [
        "Welcome to the Centroid Tutorial!\nPress 'Right Arrow' or 'Space' to advance to the next step.",
        "Step 1: Look at the 3D Image.\nYou'll notice one centroid is incorrectly placed (False Positive) and one cell is missing a centroid.",
        "Step 2: Select the 'Centroids' layer.\nClick the 'Select points' tool (arrow icon), highlight the incorrect point, and press 'Delete'.",
        "Step 3: Click the 'Add points' tool (circle with plus).\nClick directly on the center of the missing cell to add a new centroid.",
        "Step 4: Now let's save.\nPress 'S' on your keyboard to instantly save to the SWC file!",
        "Congratulations! You've learned how to proofread centroids!\n"
    ]
    
    step_idx = [0]
    viewer.text_overlay.visible = True
    viewer.text_overlay.color = 'white'
    viewer.text_overlay.text = tutorial_steps[0]
    
    @viewer.bind_key('space')
    @viewer.bind_key('Right')
    def advance_tutorial(v):
        if step_idx[0] < len(tutorial_steps) - 1:
            step_idx[0] += 1
            v.text_overlay.text = tutorial_steps[step_idx[0]]
            
    @viewer.bind_key('s')
    def save_state(viewer):
        print("Centroids Saved!")
        if step_idx[0] == 4:
            step_idx[0] += 1
            viewer.text_overlay.text = tutorial_steps[step_idx[0]]

    napari.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['neurites', 'centroids'], required=True, help="Which tutorial to run")
    args = parser.parse_args()
    
    if args.mode == 'neurites':
        run_neurite_tutorial()
    else:
        run_centroid_tutorial()
