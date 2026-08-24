import os
import argparse
import tifffile
import numpy as np
import networkx as nx

def visualize_colored_neurons(raw_volume_path, swc_path, soma_mask_path=None):
    print("Launching Napari for visualization...")
    try:
        import napari
    except ImportError:
        print("Napari is not installed. Skipping visualization.")
        return
        
    viewer = napari.Viewer(ndisplay=3)
    
    # Load raw volume
    if os.path.exists(raw_volume_path):
        print(f"Loading raw volume: {raw_volume_path}")
        raw_volume = tifffile.imread(raw_volume_path)
        
        # Hide somas if requested to keep the background clean
        if soma_mask_path and os.path.exists(soma_mask_path):
            print(f"Masking out somas using {soma_mask_path}")
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
    print(f"Initial connected components (including fragments): {len(components)}")
    
    # Keep all fragments, don't reduce the number of skeletons
    min_nodes = 2
    large_components = [c for c in components if len(c) >= min_nodes]
    print(f"Filtered down to {len(large_components)} major neurons (>= {min_nodes} nodes).")
    
    components = large_components
    
    # Generate colors
    import matplotlib
    try:
        cmap = matplotlib.colormaps.get_cmap('hsv')
    except AttributeError:
        import matplotlib.cm as cm
        cmap = cm.get_cmap('hsv')
    
    paths = []
    path_colors = []
    
    print("Building colorized neuron shapes (this may take a moment for large SWCs)...")
    for comp in components:
        # Pick a random bright color from the HSV colormap for this specific neuron
        color = cmap(np.random.rand())
        
        comp_subgraph = G.subgraph(comp)
        
        # Pick a root node (leaf if possible, else any node)
        root = next((n for n in comp_subgraph.nodes() if comp_subgraph.degree(n) == 1), list(comp_subgraph.nodes())[0])
        
        # Extract continuous branches between branch points
        branches = []
        visited = set()
        stack = [(root, [root])]
        
        while stack:
            curr, current_path = stack.pop()
            visited.add(curr)
            
            neighbors = [n for n in comp_subgraph.neighbors(curr) if n not in visited]
            
            if len(neighbors) == 1:
                # Continue the unbranched path
                current_path.append(neighbors[0])
                stack.append((neighbors[0], current_path))
            elif len(neighbors) > 1:
                # Branch point! Save the current path, and start new ones
                if len(current_path) > 1:
                    branches.append(current_path)
                for n in neighbors:
                    stack.append((n, [curr, n]))
            else:
                # Leaf node
                if len(current_path) > 1:
                    branches.append(current_path)
                    
        for branch_nodes in branches:
            # Convert list of node IDs to list of [z, y, x] coordinates
            branch_coords = [nodes[n] for n in branch_nodes]
            paths.append(branch_coords)
            path_colors.append(color)
            
    if paths:
        # Scale is removed because the SWC itself contains physical coordinates
        viewer.add_shapes(paths, shape_type='path', edge_color=path_colors, edge_width=0.5, name='Colored Neurons')
        print(f"Added {len(paths)} continuous skeleton branches across {len(components)} neurons.")
        
    napari.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--volume', required=True, help='Path to raw volume TIF')
    parser.add_argument('--swc', required=True, help='Path to SWC file')
    parser.add_argument('--soma_mask', required=False, help='Path to soma mask to hide somas from volume')
    args = parser.parse_args()
    
    visualize_colored_neurons(args.volume, args.swc, args.soma_mask)
