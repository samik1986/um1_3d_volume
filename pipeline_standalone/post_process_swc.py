import argparse
import os
import networkx as nx
import numpy as np
from scipy.interpolate import splprep, splev

def parse_swc(filepath):
    """Parses an SWC file into a NetworkX graph and a node dictionary."""
    graph = nx.Graph()
    nodes = {}
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            parts = line.split()
            if len(parts) >= 7:
                n_id = int(parts[0])
                n_type = int(parts[1])
                x = float(parts[2])
                y = float(parts[3])
                z = float(parts[4])
                radius = float(parts[5])
                parent_id = int(parts[6])
                
                nodes[n_id] = {
                    'type': n_type,
                    'x': x,
                    'y': y,
                    'z': z,
                    'r': radius,
                    'pid': parent_id
                }
                
                graph.add_node(n_id)
                if parent_id != -1:
                    graph.add_edge(n_id, parent_id)
                    
    return graph, nodes

def get_branches(graph):
    """Extracts all unbranched segments from the graph."""
    branches = []
    visited_edges = set()
    
    # Junctions are branch points (degree > 2) or endpoints (degree == 1)
    junctions = set(n for n, d in graph.degree() if d != 2)
    
    # Handle perfect rings if they exist
    if not junctions and len(graph.nodes()) > 0:
        junctions.add(list(graph.nodes())[0])
        
    for j in junctions:
        for neighbor in graph.neighbors(j):
            edge = tuple(sorted((j, neighbor)))
            if edge in visited_edges:
                continue
                
            path = [j, neighbor]
            visited_edges.add(edge)
            
            curr = neighbor
            while graph.degree(curr) == 2:
                next_node = [n for n in graph.neighbors(curr) if n != path[-2]][0]
                path.append(next_node)
                visited_edges.add(tuple(sorted((curr, next_node))))
                curr = next_node
                
            branches.append(path)
            
    return branches

def smooth_swc(filepath, output_path, smoothing_factor=2.0):
    print(f"Loading SWC: {filepath}")
    graph, nodes = parse_swc(filepath)
    print(f"Loaded {len(nodes)} nodes.")
    
    branches = get_branches(graph)
    print(f"Extracted {len(branches)} branches for smoothing.")
    
    smoothed_count = 0
    for path in branches:
        if len(path) < 4:
            continue # Too short for cubic spline
            
        # Get coordinates for the branch
        coords = np.array([[nodes[n]['x'], nodes[n]['y'], nodes[n]['z']] for n in path])
        
        # Check for overlapping points which crash splprep
        dists = np.sqrt(np.sum(np.diff(coords, axis=0)**2, axis=1))
        if np.any(dists < 1e-5):
            continue
            
        try:
            # 3D Cubic B-spline interpolation
            pts = coords.T
            tck, _ = splprep(pts, s=smoothing_factor, k=3)
            
            # Generate new points evenly spaced along the spline
            u_new = np.linspace(0, 1, len(path))
            new_pts = np.vstack(splev(u_new, tck)).T
            
            # Force endpoints to remain exactly pinned to preserve topology!
            new_pts[0] = coords[0]
            new_pts[-1] = coords[-1]
            
            # Update the node dictionary with smoothed coordinates
            for i, n in enumerate(path):
                nodes[n]['x'] = new_pts[i][0]
                nodes[n]['y'] = new_pts[i][1]
                nodes[n]['z'] = new_pts[i][2]
                
            smoothed_count += 1
            
        except Exception as e:
            # Skip branches that fail spline fitting
            pass
            
    print(f"Successfully smoothed {smoothed_count} branches.")
    
    # Write back to SWC
    print(f"Writing smoothed SWC to: {output_path}")
    with open(output_path, 'w') as f:
        f.write("# Smoothed 3D Skeletons\n")
        f.write(f"# Smoothing factor: {smoothing_factor}\n")
        f.write("# ID Type X Y Z Radius Parent\n")
        
        # Maintain original order if possible by sorting keys
        for n_id in sorted(nodes.keys()):
            n = nodes[n_id]
            f.write(f"{n_id} {n['type']} {n['x']:.2f} {n['y']:.2f} {n['z']:.2f} {n['r']:.1f} {n['pid']}\n")
            
    print("Done!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Post-process and smooth an SWC file.")
    parser.add_argument('--input', required=True, help="Input SWC file")
    parser.add_argument('--output', required=True, help="Output SWC file")
    parser.add_argument('--smooth', type=float, default=2.0, help="Spline smoothing factor (higher = smoother, default=2.0)")
    
    args = parser.parse_args()
    smooth_swc(args.input, args.output, args.smooth)
