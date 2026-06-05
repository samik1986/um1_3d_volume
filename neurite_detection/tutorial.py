"""
tutorial.py (Interactive In-App Tutorial)
"""
import os
import sys
import json
import tifffile
import napari
import numpy as np
import matplotlib.cm as cm

def load_cw_complex(json_path):
    with open(json_path, 'r') as f:
        return json.load(f)

def run_tutorial():
    raw_vol_path = "tutorial_data/tutorial_crop.tif"
    somas_path = "output/tutorial_crop/soma_labels.tif"
    mask_vol_path = "output/tutorial_crop/neurite_mask.tif"
    cw_json_path = "output/tutorial_crop/cw_complex.json"
    
    if not os.path.exists(raw_vol_path) or not os.path.exists(cw_json_path):
        print("Tutorial data not found! Please ensure create_tutorial_data.py has been run.")
        return

    raw_vol = tifffile.imread(raw_vol_path, out='memmap')
    cw_data = load_cw_complex(cw_json_path)
    
    viewer = napari.Viewer(title="Interactive Proofreading Tutorial")
    voxel_scale = (0.5, 0.1102, 0.1102)
    
    p1, p99 = np.percentile(raw_vol[::2, ::2, ::2], (1, 99.9))
    viewer.add_image(
        raw_vol, 
        name='Raw Volume', 
        scale=voxel_scale,
        colormap='magenta', 
        blending='additive',
        contrast_limits=[p1, p99]
    )
    
    if os.path.exists(mask_vol_path):
        mask_vol = tifffile.imread(mask_vol_path, out='memmap')
        viewer.add_labels(mask_vol, name='Binary Mask', scale=voxel_scale, opacity=0.3, visible=False)
        
    soma_color_dict = None
    if os.path.exists(somas_path):
        soma_labels = tifffile.imread(somas_path, out='memmap')
        soma_layer = viewer.add_labels(soma_labels, name='Detected Somas', scale=voxel_scale, opacity=0.8)
        
        np.random.seed(42)
        unique_somas = np.unique(soma_labels)
        base_colors = cm.tab20(np.linspace(0, 1, 20))
        np.random.shuffle(base_colors)
        
        soma_color_dict = {0: [0, 0, 0, 0]}
        for i, sid in enumerate(unique_somas):
            if sid == 0: continue
            soma_color_dict[sid] = base_colors[i % 20]
        soma_layer.color = soma_color_dict
    
    nodes = cw_data.get('cells_0_nodes', [])
    node_coords = [n['coord'] for n in nodes]
    node_types = [n['type'] for n in nodes]
    face_colors = ['blue' if t == 'junction' else 'red' for t in node_types]
    
    if node_coords:
        viewer.add_points(
            np.array(node_coords),
            name='0-Cells (Nodes)',
            size=3,
            face_color=face_colors,
            scale=voxel_scale
        )
    
    lines = cw_data.get('cells_1_linestrings', [])
    line_paths = [l['geometry'] for l in lines]
    comp_ids = [l.get('component_id', -999) for l in lines]
    
    edge_colors = []
    if soma_color_dict:
        for cid in comp_ids:
            if cid in soma_color_dict:
                edge_colors.append(soma_color_dict[cid])
            else:
                idx = abs(cid) % 20
                edge_colors.append(base_colors[idx])
    else:
        edge_colors = 'green'
    
    if line_paths:
        viewer.add_shapes(
            line_paths,
            shape_type='path',
            edge_color=edge_colors,
            edge_width=2,
            name='1-Cells (Edges)',
            scale=voxel_scale
        )
        
    # --- TUTORIAL LOGIC ---
    tutorial_steps = [
        "Welcome to the Interactive Tutorial!\nPress 'Right Arrow' or 'Space' to advance to the next step.",
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
        print("Extracting and snapping updated geometry...")
        nodes_data = viewer.layers['0-Cells (Nodes)'].data if '0-Cells (Nodes)' in viewer.layers else []
        paths_layer_name = '1-Cells (Edges)'
        paths_data = viewer.layers[paths_layer_name].data if paths_layer_name in viewer.layers else []
        
        threshold = 8.0 
        all_path_points = []
        for p in paths_data:
            for pt in p:
                all_path_points.append(pt)
        all_path_points = np.array(all_path_points) if len(all_path_points) > 0 else np.array([])
        
        snapped_paths = []
        for p in paths_data:
            new_p = np.copy(p)
            if len(new_p) > 0 and len(all_path_points) > 0:
                dists_s = np.linalg.norm(all_path_points - new_p[0], axis=1)
                dists_s[dists_s == 0] = np.inf
                min_s = np.argmin(dists_s)
                if dists_s[min_s] < threshold:
                    new_p[0] = all_path_points[min_s]
                
                dists_e = np.linalg.norm(all_path_points - new_p[-1], axis=1)
                dists_e[dists_e == 0] = np.inf
                min_e = np.argmin(dists_e)
                if dists_e[min_e] < threshold:
                    new_p[-1] = all_path_points[min_e]
            snapped_paths.append(new_p)
            
        snapped_nodes = []
        if len(all_path_points) > 0:
            for n in nodes_data:
                dists = np.linalg.norm(all_path_points - n, axis=1)
                min_idx = np.argmin(dists)
                if dists[min_idx] < threshold:
                    snapped_nodes.append(all_path_points[min_idx])
                else:
                    snapped_nodes.append(n)
        else:
            snapped_nodes = nodes_data
            
        if '0-Cells (Nodes)' in viewer.layers:
            viewer.layers['0-Cells (Nodes)'].data = np.array(snapped_nodes) if len(snapped_nodes) > 0 else np.empty((0,3))
        if paths_layer_name in viewer.layers:
            viewer.layers[paths_layer_name].data = snapped_paths
            
        print("Snapped successfully!")
        
        # Advance tutorial automatically if at save step
        if step_idx[0] == 4:
            step_idx[0] += 1
            viewer.text_overlay.text = tutorial_steps[step_idx[0]]

    napari.run()

if __name__ == '__main__':
    run_tutorial()
