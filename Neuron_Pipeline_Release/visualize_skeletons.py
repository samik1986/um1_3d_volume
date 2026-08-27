"""
visualize_skeletons.py (neurite_detection)

Author: Samik Banerjee
Last updated on: August 28, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

Napari-based interactive 3D viewer for SWC files overlaid on volume data.
"""
import os
import argparse
import tifffile
import numpy as np
import networkx as nx

def visualize_skeletons(raw_volume_path, mask_path, swc_path, soma_path, scale_z, scale_y, scale_x):
    print("Launching Napari for unified visualization...")
    try:
        import napari
    except ImportError:
        print("Napari is not installed. Skipping visualization.")
        return
        
    viewer = napari.Viewer(ndisplay=3)
    
    # Helper to safely load and downsample if needed
    def load_and_downsample(path):
        vol = tifffile.imread(path)
        vol = np.asarray(vol)
        sy, sx = scale_y, scale_x
        if vol.shape[1] > 2048 or vol.shape[2] > 2048:
            print(f"Manually downsampling {os.path.basename(path)} to fit GL_MAX_TEXTURE_SIZE...")
            vol = vol[:, ::2, ::2]
            sy, sx = scale_y * 2, scale_x * 2
        return np.ascontiguousarray(vol), (scale_z, sy, sx)

    # 1. Load raw volume
    if os.path.exists(raw_volume_path):
        print(f"Loading raw volume: {raw_volume_path}")
        raw_volume, scale_raw = load_and_downsample(raw_volume_path)
        viewer.add_image(raw_volume, name='Raw Volume', colormap='gray', blending='additive', scale=scale_raw)
    else:
        print(f"Warning: Raw volume not found at {raw_volume_path}")
        
    # 2. Load skeleton mask
    if mask_path and os.path.exists(mask_path):
        print(f"Loading skeleton mask: {mask_path}")
        mask, scale_mask = load_and_downsample(mask_path)
        viewer.add_image(mask, name='Skeleton Mask', colormap='red', blending='additive', scale=scale_mask, opacity=0.8, visible=True)
    else:
        print(f"Warning: Skeleton mask not found or not provided: {mask_path}")

    # 2.5 Load soma mask
    if soma_path and os.path.exists(soma_path):
        print(f"Loading soma labels: {soma_path}")
        soma_mask, scale_soma = load_and_downsample(soma_path)
        viewer.add_labels(soma_mask, name='Soma Labels', scale=scale_soma, opacity=0.7, visible=True)
    elif soma_path:
        print(f"Warning: Soma mask not found: {soma_path}")

    # 3. Parse and load SWC Vectors
    if swc_path and os.path.exists(swc_path):
        print(f"Parsing SWC: {swc_path}")
        nodes = {}
        edges = []
        
        with open(swc_path, 'r') as f:
            for line in f:
                if line.startswith('#') or not line.strip(): continue
                parts = line.strip().split()
                if len(parts) >= 7:
                    n_id = int(parts[0])
                    # SWC is standard X, Y, Z
                    x, y, z = float(parts[2]), float(parts[3]), float(parts[4])
                    parent = int(parts[6])
                    # Store as Z, Y, X for Napari which expects (D, H, W) coordinates
                    nodes[n_id] = (z, y, x)
                    if parent != -1:
                        edges.append((parent, n_id))
        # Build graph to find connected components (individual neurons)
        G = nx.Graph()
        G.add_nodes_from(nodes.keys())
        G.add_edges_from(edges)
        
        components = list(nx.connected_components(G))
        print(f"Found {len(components)} skeleton components.")
        
        paths = []
        path_colors = []
        
        print("Building neuron vectors (continuous connected lines)...")
        for comp in components:
            color = 'red'
            comp_subgraph = G.subgraph(comp)
            
            # Find a root node (degree 1)
            try:
                root = next(n for n in comp_subgraph.nodes() if comp_subgraph.degree(n) == 1)
            except StopIteration:
                root = list(comp_subgraph.nodes())[0]
                
            branches = []
            visited = set()
            stack = [(root, [root])]
            
            while stack:
                curr, current_path = stack.pop()
                visited.add(curr)
                
                neighbors = [n for n in comp_subgraph.neighbors(curr) if n not in visited]
                
                if len(neighbors) == 1:
                    current_path.append(neighbors[0])
                    stack.append((neighbors[0], current_path))
                elif len(neighbors) > 1:
                    if len(current_path) > 1:
                        branches.append(current_path)
                    for n in neighbors:
                        # Start new branch from current junction
                        stack.append((n, [curr, n]))
                else:
                    if len(current_path) > 1:
                        branches.append(current_path)
                        
            for branch_nodes in branches:
                branch_coords = [nodes[n] for n in branch_nodes]
                paths.append(branch_coords)
                path_colors.append(color)
                
        if paths:
            viewer.add_shapes(paths, shape_type='path', edge_color=path_colors, edge_width=2.0, name='Vector Skeletons (SWC)', scale=(scale_z, scale_y, scale_x))
            print(f"Added {len(paths)} continuous skeleton branches.")
    else:
        print(f"Warning: SWC not found or not provided: {swc_path}")
        
    napari.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Unified Visualization of Raw Volume, Skeleton Mask, and SWC Vectors")
    parser.add_argument('--volume', required=True, help='Path to raw volume TIF')
    parser.add_argument('--mask', required=False, help='Path to skeleton mask TIF')
    parser.add_argument('--swc', required=False, help='Path to SWC vectors')
    parser.add_argument('--soma', required=False, help='Path to soma labels TIF')
    parser.add_argument('--scale_z', type=float, default=0.5, help="Physical scale of Z axis")
    parser.add_argument('--scale_y', type=float, default=0.1102, help="Physical scale of Y axis")
    parser.add_argument('--scale_x', type=float, default=0.112, help="Physical scale of X axis")
    args = parser.parse_args()
    
    visualize_skeletons(args.volume, args.mask, args.swc, args.soma, args.scale_z, args.scale_y, args.scale_x)
