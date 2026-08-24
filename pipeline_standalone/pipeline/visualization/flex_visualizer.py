"""
flex_visualizer.py (neurite_detection/pipeline/visualization)

Author: Samik Banerjee
Date: June 10, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

A flexible visualizer that dynamically loads unlimited layers of various extensions.
"""

import os
import sys
import json
import numpy as np
import tifffile
import napari
import argparse

def main():
    parser = argparse.ArgumentParser(description="Flexible Napari Visualizer for N layers")
    parser.add_argument("layers", nargs='*', help="Paths to any number of .tif, .npy, .swc, or .json files")
    args = parser.parse_args()
    
    if not args.layers:
        print("No layers provided. Launching empty Napari viewer.")
        print("Usage: python flex_visualizer.py [file1.tif] [file2.npy] [file3.swc] [file4.json] ...")
        
    print("\n--- Launching Flexible Napari Visualizer ---")
    viewer = napari.Viewer(ndisplay=3)
    
    for filepath in args.layers:
        if not os.path.exists(filepath):
            print(f"[WARNING] File not found: {filepath}")
            continue
            
        ext = os.path.splitext(filepath)[1].lower()
        name = os.path.basename(filepath)
        
        print(f"Loading {name}...")
        
        if ext in ['.tif', '.tiff']:
            try:
                img = tifffile.memmap(filepath)
            except ValueError:
                img = tifffile.imread(filepath)
            viewer.add_image(img, name=name, blending='additive')
            
        elif ext == '.npy':
            arr = np.load(filepath)
            if arr.dtype == bool or np.issubdtype(arr.dtype, np.integer):
                viewer.add_labels(arr, name=name, opacity=0.7)
            else:
                viewer.add_image(arr, name=name, blending='additive')
                
        elif ext == '.json':
            with open(filepath, 'r') as fp:
                try:
                    data = json.load(fp)
                except json.JSONDecodeError as e:
                    print(f"[ERROR] Failed to parse JSON {name}: {e}")
                    continue
            
            nodes = data.get("cells_0_nodes", [])
            lines = data.get("cells_1_linestrings", [])
            
            coords = []
            for n in nodes:
                # Expects [z, y, x]
                coords.append(n["coord"])
                
            if coords:
                viewer.add_points(np.array(coords), name=f"{name} (Nodes)", size=2.0, face_color='red')
                
            paths = []
            for l in lines:
                # Geometry is [[z1, y1, x1], [z2, y2, x2]]
                paths.append(np.array(l["geometry"]))
                
            if paths:
                viewer.add_shapes(paths, shape_type='path', name=f"{name} (Edges)", edge_color='cyan', edge_width=1.0)
                
        elif ext == '.swc':
            nodes = {}
            paths = []
            with open(filepath, 'r') as fp:
                for line in fp:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split()
                    if len(parts) >= 7:
                        nid = int(parts[0])
                        # SWC standard: id type x y z radius parent_id
                        # We map to Napari Z, Y, X
                        x, y, z = float(parts[2]), float(parts[3]), float(parts[4])
                        pid = int(parts[6])
                        nodes[nid] = [z, y, x]
                        
                        if pid != -1 and pid in nodes:
                            paths.append(np.array([nodes[pid], [z, y, x]]))
            
            if paths:
                viewer.add_shapes(paths, shape_type='path', name=name, edge_color='magenta', edge_width=1.0)
        else:
            print(f"[WARNING] Unsupported file extension for {name}. Skipping.")

    print("All layers loaded. Starting Napari GUI...")
    napari.run()

if __name__ == "__main__":
    main()
