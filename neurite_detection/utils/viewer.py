"""
viewer.py (neurite_detection)

Author: Samik Banerjee
Date: June 5, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

Interactive Napari viewer for proofreading topological CW Complex networks of neurites.
"""

import os
import sys
import json
import argparse
import tifffile
import napari
import numpy as np

def load_cw_complex(json_path):
    with open(json_path, 'r') as f:
        return json.load(f)

def save_cw_complex(cw_data, json_path):
    with open(json_path, 'w') as f:
        json.dump(cw_data, f, indent=2)
    print(f"Saved updated CW Complex to {json_path}")

def run_viewer(raw_vol_path, cw_json_path, mask_vol_path=None, somas_path=None):
    print("Loading raw volume...")
    raw_vol = tifffile.imread(raw_vol_path, out='memmap')
    
    cw_data = load_cw_complex(cw_json_path)
    
    print("Opening Napari Viewer...")
    viewer = napari.Viewer(title="Neurite CW Complex Proofreading Viewer")
    
    voxel_scale = (0.5, 0.1102, 0.1102)
    
    print("Calculating contrast limits for Raw Volume...")
    p1, p99 = np.percentile(raw_vol[::10, ::10, ::10], (1, 99.9))
    print(f"Contrast limits: {p1} - {p99}")
    
    viewer.add_image(
        raw_vol, 
        name='Raw Volume', 
        scale=voxel_scale,
        colormap='magenta', 
        blending='additive',
        contrast_limits=[p1, p99]
    )
    
    if mask_vol_path and os.path.exists(mask_vol_path):
        mask_vol = tifffile.imread(mask_vol_path, out='memmap')
        viewer.add_labels(
            mask_vol,
            name='Binary Mask',
            scale=voxel_scale,
            opacity=0.3,
            visible=False
        )
        
    soma_color_dict = None
    if somas_path and os.path.exists(somas_path):
        soma_labels = tifffile.imread(somas_path, out='memmap')
        soma_layer = viewer.add_labels(
            soma_labels,
            name='Detected Somas',
            scale=voxel_scale,
            opacity=0.8
        )
        # Napari assigns a random colormap by default to labels
        # We can extract it or build our own to sync with the shapes.
        import matplotlib.cm as cm
        np.random.seed(42)
        unique_somas = np.unique(soma_labels)
        base_colors = cm.tab20(np.linspace(0, 1, 20))
        np.random.shuffle(base_colors)
        
        soma_color_dict = {0: [0, 0, 0, 0]}
        for i, sid in enumerate(unique_somas):
            if sid == 0: continue
            soma_color_dict[sid] = base_colors[i % 20]
            
        soma_layer.color = soma_color_dict
    
    # Render CW Complex 0-Cells
    nodes = cw_data.get('cells_0_nodes', [])
    node_coords = [n['coord'] for n in nodes]
    node_types = [n['type'] for n in nodes]
    
    # Differentiate junction vs boundary
    face_colors = ['blue' if t == 'junction' else 'red' for t in node_types]
    
    if node_coords:
        pts_layer = viewer.add_points(
            np.array(node_coords),
            name='0-Cells (Nodes)',
            size=3,
            face_color=face_colors,
            scale=voxel_scale
        )
    
    # Render CW Complex 1-Cells
    lines = cw_data.get('cells_1_linestrings', [])
    line_paths = [l['geometry'] for l in lines]
    comp_ids = [l.get('component_id', -999) for l in lines]
    
    edge_colors = []
    if soma_color_dict:
        # Match colors to somas, use random for orphans
        for cid in comp_ids:
            if cid in soma_color_dict:
                edge_colors.append(soma_color_dict[cid])
            else:
                # Orphan IDs are negative
                idx = abs(cid) % 20
                edge_colors.append(base_colors[idx])
    else:
        # Generic coloring if no somas
        edge_colors = 'green'
    
    if line_paths:
        shapes_layer = viewer.add_shapes(
            line_paths,
            shape_type='path',
            edge_color=edge_colors,
            edge_width=2,
            name='1-Cells (Connected Neurons)',
            scale=voxel_scale
        )
        
    print("Viewer ready. Proofreading Instructions:")
    print(" - Select '0-Cells (Nodes)' layer to add/delete/move junctions and endpoints.")
    print(" - Select '1-Cells (Edges)' layer to modify the paths.")
    print(" - Press 'S' to save the current state back to JSON.")
    
    @viewer.bind_key('s')
    def save_state(viewer):
        print("Extracting and snapping updated geometry...")
        
        nodes_data = viewer.layers['0-Cells (Nodes)'].data if '0-Cells (Nodes)' in viewer.layers else []
        paths_layer_name = '1-Cells (Connected Neurons)' if '1-Cells (Connected Neurons)' in viewer.layers else '1-Cells (Edges)'
        paths_data = viewer.layers[paths_layer_name].data if paths_layer_name in viewer.layers else []
        
        # --- SNAPPING LOGIC ---
        # Snap edge endpoints to the nearest neurite centerline point to maintain continuity
        threshold = 8.0  # pixels
        
        all_path_points = []
        for p in paths_data:
            for pt in p:
                all_path_points.append(pt)
        all_path_points = np.array(all_path_points) if len(all_path_points) > 0 else np.array([])
        
        snapped_paths = []
        for p in paths_data:
            new_p = np.copy(p)
            if len(new_p) > 0 and len(all_path_points) > 0:
                # Snap Start
                dists_s = np.linalg.norm(all_path_points - new_p[0], axis=1)
                dists_s[dists_s == 0] = np.inf # Ignore exact same point
                min_s = np.argmin(dists_s)
                if dists_s[min_s] < threshold:
                    new_p[0] = all_path_points[min_s]
                
                # Snap End
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
            
        # Visually update the viewer layers with the snapped geometry
        if '0-Cells (Nodes)' in viewer.layers:
            viewer.layers['0-Cells (Nodes)'].data = np.array(snapped_nodes) if len(snapped_nodes) > 0 else np.empty((0,3))
        if paths_layer_name in viewer.layers:
            viewer.layers[paths_layer_name].data = snapped_paths
            
        # --- SAVE TO JSON ---
        if '0-Cells (Nodes)' in viewer.layers:
            cw_data['cells_0_nodes'] = [
                {
                    "node_id": i,
                    "type": "edited",
                    "coord": [int(c[0]), int(c[1]), int(c[2])]
                } for i, c in enumerate(snapped_nodes)
            ]
            
        if paths_layer_name in viewer.layers:
            cw_data['cells_1_linestrings'] = [
                {
                    "line_id": i + 1,
                    "endpoints": {"source_id": -1, "target_id": -1}, # Approximation for proofread
                    "geometry": [[int(c[0]), int(c[1]), int(c[2])] for c in p],
                    "forest_relation": {"connects": ["edited", "edited"]},
                    "radius": [1.0] * len(p)
                } for i, p in enumerate(snapped_paths)
            ]
            
        save_cw_complex(cw_data, cw_json_path)

    napari.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw', required=True, help="Input raw TIFF")
    parser.add_argument('--cw', required=True, help="Input CW Complex JSON")
    parser.add_argument('--mask', help="Input binary mask TIFF (optional)")
    parser.add_argument('--somas', help="Input Soma Labels TIFF (optional)")
    args = parser.parse_args()
    
    run_viewer(args.raw, args.cw, args.mask, args.somas)
