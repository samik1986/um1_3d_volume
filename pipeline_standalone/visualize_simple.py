import os
import argparse
import tifffile
import numpy as np

def visualize_simple(raw_volume_path, swc_path, soma_mask_path=None):
    print("Launching Napari for visualization...")
    import napari
        
    viewer = napari.Viewer(ndisplay=3)
    
    # Load raw volume
    if os.path.exists(raw_volume_path):
        print(f"Loading raw volume: {raw_volume_path}")
        raw_volume = tifffile.imread(raw_volume_path)
        
        # Hide somas
        if soma_mask_path and os.path.exists(soma_mask_path):
            soma_mask = tifffile.imread(soma_mask_path)
            raw_volume[soma_mask > 0] = 0
            
        # Display with correct physical Z, Y, X scale
        viewer.add_image(raw_volume, name='Raw Volume', colormap='gray', blending='additive', scale=(0.5, 0.1102, 0.1102))
    
    # Parse SWC
    print(f"Parsing SWC: {swc_path}")
    nodes = {}
    edges = []
    
    with open(swc_path, 'r') as f:
        for line in f:
            if line.startswith('#') or not line.strip(): continue
            parts = line.strip().split()
            if len(parts) >= 7:
                n_id = int(parts[0])
                # SWC is X, Y, Z
                x, y, z = float(parts[2]), float(parts[3]), float(parts[4])
                parent = int(parts[6])
                # Store as Z, Y, X to match the numpy array dimensions of the volume
                nodes[n_id] = (z, y, x)
                if parent != -1:
                    edges.append((parent, n_id))
                    
    paths = []
    for u, v in edges:
        if u in nodes and v in nodes:
            paths.append([nodes[u], nodes[v]])
            
    if paths:
        # Display shapes without scaling because the SWC file itself contains physical coordinates now
        viewer.add_shapes(paths, shape_type='path', edge_color='red', edge_width=0.5, name='Skeletons')
        print(f"Added {len(paths)} skeleton segments.")
        
    napari.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--volume', required=True)
    parser.add_argument('--swc', required=True)
    parser.add_argument('--soma_mask', required=False)
    args = parser.parse_args()
    visualize_simple(args.volume, args.swc, args.soma_mask)
