"""
trace_and_connect_skeletons.py (neurite_detection)

Author: Samik Banerjee
Date: August 28, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

Graph-based backbone tracing, pruning, and micron-scaling of 3D skeletons.
"""
import argparse
import tifffile
import numpy as np
from scipy.spatial import cKDTree
import networkx as nx
import time

def extract_connected_swc(mask_path, output_path, valid_mask_path=None, gap_dist_px=15, sample_rate=5, scale_z=0.5, scale_y=0.1102, scale_x=0.112):
    t0 = time.time()
    
    print(f"Loading skeleton mask: {mask_path}")
    mask = tifffile.imread(mask_path)
    
    print("Extracting non-zero coordinates...")
    coords = np.argwhere(mask > 0)
    print(f"Found {len(coords)} raw skeleton voxels.")
    
    if valid_mask_path:
        print(f"Loading valid regions mask: {valid_mask_path}")
        valid_vol = tifffile.imread(valid_mask_path)
        print("Filtering out skeleton voxels that fall outside the valid regions (e.g., removing somas)...")
        valid_idx = valid_vol[coords[:, 0], coords[:, 1], coords[:, 2]] > 0
        coords = coords[valid_idx]
        print(f"Kept {len(coords)} valid dendrite skeleton voxels.")
        
    if len(coords) == 0:
        print("Mask is empty. Exiting.")
        return
        
    print("Building KDTree for 26-connectivity...")
    tree = cKDTree(coords)
    
    print("Finding 26-connected neighbors (r=1.75)...")
    pairs = tree.query_pairs(r=1.75)
    
    print("Building base skeleton graph...")
    G = nx.Graph()
    G.add_edges_from(pairs)
    G.add_nodes_from(range(len(coords)))
    
    print(f"Base graph components: {nx.number_connected_components(G)}")
    
    print(f"Identifying endpoints for bridging gaps...")
    endpoints = [n for n in G.nodes() if G.degree(n) == 1]
    
    if endpoints:
        print(f"Found {len(endpoints)} endpoints. Finding connections within {gap_dist_px} pixels...")
        ep_coords = coords[endpoints]
        ep_tree = cKDTree(ep_coords)
        
        ep_pairs = ep_tree.query_pairs(r=gap_dist_px)
        
        edges_to_add = []
        for i, j in ep_pairs:
            orig_i, orig_j = endpoints[i], endpoints[j]
            edges_to_add.append((orig_i, orig_j))
            
        print(f"Adding {len(edges_to_add)} bridging edges between disconnected dendrites...")
        G.add_edges_from(edges_to_add)
        print(f"Graph components after bridging: {nx.number_connected_components(G)}")
    
    print("Pruning small isolated noise components after bridging...")
    components = list(nx.connected_components(G))
    to_remove = []
    for comp in components:
        # A threshold of 200 nodes (~22 microns) will safely delete all noise speckles.
        # Real faint neurons have already been stitched together into massive trees by bridging!
        if len(comp) < 200:
            to_remove.extend(comp)
            
    G.remove_nodes_from(to_remove)
    print(f"Removed {len(to_remove)} noise nodes. Remaining components: {nx.number_connected_components(G)}")

    print("Extracting branches and subsampling nodes...")
    junctions = set(n for n, d in G.degree() if d > 2)
    new_endpoints = set(n for n, d in G.degree() if d == 1)
    
    if not junctions and not new_endpoints and len(G.nodes) > 0:
        junctions.add(list(G.nodes)[0])
        
    terminals = junctions.union(new_endpoints)
    
    visited_edges = set()
    branches = []
    
    for t in terminals:
        for neighbor in G.neighbors(t):
            edge = tuple(sorted((t, neighbor)))
            if edge in visited_edges:
                continue
                
            path = [t, neighbor]
            visited_edges.add(edge)
            
            curr = neighbor
            while G.degree(curr) == 2:
                next_node = [n for n in G.neighbors(curr) if n != path[-2]][0]
                path.append(next_node)
                visited_edges.add(tuple(sorted((curr, next_node))))
                curr = next_node
                
            branches.append(path)
            
    print(f"Extracted {len(branches)} branch segments.")
    
    # Prune small branches and twigs
    pruned_branches = []
    for branch in branches:
        deg1 = G.degree(branch[0])
        deg2 = G.degree(branch[-1])
        
        is_ep1 = deg1 == 1
        is_ep2 = deg2 == 1
        
        if is_ep1 and is_ep2:
            # Isolated line
            if len(branch) >= 150:
                pruned_branches.append(branch)
        elif is_ep1 or is_ep2:
            # Twig connected to a junction
            if len(branch) >= 80:
                pruned_branches.append(branch)
        else:
            # Backbone (junction to junction)
            # Deleting extremely short backbones (<15) prevents ultra-dense mesh hubs from forming.
            if len(branch) >= 15:
                pruned_branches.append(branch)
            
    print(f"Pruned down to {len(pruned_branches)} branch segments.")
    
    sampled_branches = []
    for branch in pruned_branches:
        if len(branch) <= sample_rate:
            sampled_branches.append(branch)
        else:
            sub_branch = branch[::sample_rate]
            if sub_branch[-1] != branch[-1]:
                sub_branch.append(branch[-1])
            sampled_branches.append(sub_branch)
            
    print("Reconstructing minimal spanning SWC tree structure to prevent cycles...")
    final_G = nx.Graph()
    for branch in sampled_branches:
        for i in range(len(branch) - 1):
            final_G.add_edge(branch[i], branch[i+1])
            
    swc_nodes = {}
    current_swc_id = 1
    node_to_swcid = {}
    
    for comp in nx.connected_components(final_G):
        subG = final_G.subgraph(comp)
        
        try:
            tree_graph = nx.minimum_spanning_tree(subG)
        except nx.NetworkXException:
            tree_graph = subG
            
        degrees = dict(tree_graph.degree())
        if not degrees: continue
        root = max(degrees, key=degrees.get)
        
        bfs_edges = list(nx.bfs_edges(tree_graph, root))
        
        if root not in node_to_swcid:
            node_to_swcid[root] = current_swc_id
            current_swc_id += 1
            
        swc_nodes[node_to_swcid[root]] = {'pid': -1, 'orig_idx': root}
        
        for parent, child in bfs_edges:
            if child not in node_to_swcid:
                node_to_swcid[child] = current_swc_id
                current_swc_id += 1
                
            swc_nodes[node_to_swcid[child]] = {
                'pid': node_to_swcid[parent],
                'orig_idx': child
            }
            
    microns_output_path = output_path.replace('.swc', '_microns.swc')
    print(f"Writing {len(swc_nodes)} nodes to {output_path} (subsampled by {sample_rate}x)...")
    print(f"Also saving a physical-scale copy in microns to {microns_output_path}...")
    
    with open(output_path, 'w') as f, open(microns_output_path, 'w') as f_microns:
        f.write("# Connected and Subsampled Skeletons (Pixels)\n")
        f.write(f"# Gap distance px: {gap_dist_px}, Sample rate: {sample_rate}\n")
        f.write("# ID Type X Y Z Radius Parent\n")
        
        f_microns.write("# Connected and Subsampled Skeletons (Microns)\n")
        f_microns.write(f"# Gap distance px: {gap_dist_px}, Sample rate: {sample_rate}\n")
        f_microns.write(f"# Scales: X={scale_x}, Y={scale_y}, Z={scale_z} microns/px\n")
        f_microns.write("# ID Type X_um Y_um Z_um Radius Parent\n")
        
        for n_id in range(1, current_swc_id):
            if n_id not in swc_nodes: continue
            
            node_info = swc_nodes[n_id]
            pid = node_info['pid']
            orig_idx = node_info['orig_idx']
            
            z, y, x = coords[orig_idx]
            
            # Save strictly in original voxel (pixel) coordinates to align perfectly with the raw volume
            # Napari applies the physical scaling dynamically at visualization time.
            f.write(f"{n_id} 3 {x:.2f} {y:.2f} {z:.2f} 1.0 {pid}\n")
            
            # Save in physical micron coordinates
            x_um = x * scale_x
            y_um = y * scale_y
            z_um = z * scale_z
            f_microns.write(f"{n_id} 3 {x_um:.4f} {y_um:.4f} {z_um:.4f} 1.0 {pid}\n")
            
    print(f"Total time: {time.time()-t0:.2f}s")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mask', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--valid_mask', default=None, help="Optional binary mask to filter skeleton nodes (e.g., dendrite_mask to remove somas)")
    parser.add_argument('--gap', type=float, default=15, help="Max gap distance in pixels to connect")
    parser.add_argument('--sample_rate', type=int, default=5, help="Keep 1 node every N pixels")
    # Kept scale arguments for backwards compatibility, but they are no longer used for SWC writing
    parser.add_argument('--scale_z', type=float, default=0.5)
    parser.add_argument('--scale_y', type=float, default=0.1102)
    parser.add_argument('--scale_x', type=float, default=0.112)
    
    args = parser.parse_args()
    extract_connected_swc(args.mask, args.output, args.valid_mask, args.gap, args.sample_rate, args.scale_z, args.scale_y, args.scale_x)
