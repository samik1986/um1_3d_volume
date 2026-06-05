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

def run_viewer(raw_vol_path, cw_json_path, mask_vol_path=None):
    print("Loading raw volume...")
    raw_vol = tifffile.imread(raw_vol_path, out='memmap')
    
    cw_data = load_cw_complex(cw_json_path)
    
    print("Opening Napari Viewer...")
    viewer = napari.Viewer(title="Neurite CW Complex Proofreading Viewer")
    
    voxel_scale = (1.0, 1.0, 1.0)
    
    viewer.add_image(
        raw_vol, 
        name='Raw Volume', 
        scale=voxel_scale,
        colormap='magenta', 
        blending='additive'
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
    
    if line_paths:
        shapes_layer = viewer.add_shapes(
            line_paths,
            shape_type='path',
            edge_color='green',
            edge_width=1,
            name='1-Cells (Edges)',
            scale=voxel_scale
        )
        
    print("Viewer ready. Proofreading Instructions:")
    print(" - Select '0-Cells (Nodes)' layer to add/delete/move junctions and endpoints.")
    print(" - Select '1-Cells (Edges)' layer to modify the paths.")
    print(" - Press 'S' to save the current state back to JSON.")
    
    @viewer.bind_key('s')
    def save_state(viewer):
        print("Extracting updated geometry...")
        # Update 0-cells
        if '0-Cells (Nodes)' in viewer.layers:
            pts = viewer.layers['0-Cells (Nodes)'].data
            cw_data['cells_0_nodes'] = [
                {
                    "node_id": i,
                    "type": "edited",
                    "coord": [int(c[0]), int(c[1]), int(c[2])]
                } for i, c in enumerate(pts)
            ]
            
        # Update 1-cells
        if '1-Cells (Edges)' in viewer.layers:
            paths = viewer.layers['1-Cells (Edges)'].data
            cw_data['cells_1_linestrings'] = [
                {
                    "line_id": i + 1,
                    "endpoints": {"source_id": -1, "target_id": -1}, # Approximation for proofread
                    "geometry": [[int(c[0]), int(c[1]), int(c[2])] for c in p],
                    "forest_relation": {"connects": ["edited", "edited"]},
                    "radius": [1.0] * len(p)
                } for i, p in enumerate(paths)
            ]
            
        save_cw_complex(cw_data, cw_json_path)

    napari.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw', required=True, help="Input raw TIFF")
    parser.add_argument('--cw', required=True, help="Input CW Complex JSON")
    parser.add_argument('--mask', help="Input binary mask TIFF (optional)")
    args = parser.parse_args()
    
    run_viewer(args.raw, args.cw, args.mask)
