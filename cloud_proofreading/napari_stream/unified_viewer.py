import os
import sys
import json
import argparse
import tifffile
import napari
import numpy as np
from scipy.spatial import KDTree
import networkx as nx

def parse_swc_skeleton(filepath):
    """Parses an SWC file into paths (lines) and extracts original attributes."""
    nodes = {}
    graph = nx.Graph()
    with open(filepath, 'r') as f:
        for line in f:
            if line.startswith('#') or not line.strip(): continue
            parts = line.strip().split()
            if len(parts) >= 7:
                nid = int(parts[0])
                ntype = int(parts[1])
                x, y, z = float(parts[2]), float(parts[3]), float(parts[4])
                radius = float(parts[5])
                parent = int(parts[6])
                nodes[nid] = {'coord': [z, y, x], 'type': ntype, 'radius': radius}
                graph.add_node(nid)
                if parent != -1 and parent in nodes:
                    graph.add_edge(parent, nid)
                    
    # Extract simple paths between branching points or endpoints
    paths = []
    # Identify branch points (degree > 2) and endpoints (degree == 1)
    key_nodes = set(n for n in graph.nodes if graph.degree(n) != 2)
    
    # If the graph has no branch points or endpoints (e.g., a perfect circle), just pick an arbitrary node
    if not key_nodes and len(graph.nodes) > 0:
        key_nodes.add(list(graph.nodes)[0])

    visited_edges = set()
    
    for start_node in key_nodes:
        for neighbor in graph.neighbors(start_node):
            edge = tuple(sorted((start_node, neighbor)))
            if edge in visited_edges: continue
            
            # Trace path
            current_path = [start_node]
            curr = neighbor
            prev = start_node
            visited_edges.add(edge)
            
            while curr not in key_nodes:
                current_path.append(curr)
                neighbors = list(graph.neighbors(curr))
                next_node = neighbors[0] if neighbors[0] != prev else neighbors[1]
                
                edge = tuple(sorted((curr, next_node)))
                visited_edges.add(edge)
                prev = curr
                curr = next_node
                
            current_path.append(curr)
            
            paths.append([nodes[n]['coord'] for n in current_path])
            
    # Also return a flat list of original attributes for KDTree lookup
    original_points = []
    original_attrs = []
    for nid, data in nodes.items():
        original_points.append(data['coord'])
        original_attrs.append({'type': data['type'], 'radius': data['radius']})
        
    return paths, np.array(original_points), original_attrs


def save_swc_skeleton(filepath, paths, original_points, original_attrs):
    """
    Saves edited napari paths back to an SWC format.
    Uses a KD-Tree to preserve original types and radiuses if nodes were slightly moved.
    """
    tree = KDTree(original_points) if len(original_points) > 0 else None
    
    swc_lines = ["# Unified Proofreading SWC Export\n"]
    node_id = 1
    
    # We will build a set of points. If two paths share an endpoint precisely, they share the parent.
    # To do this, we map stringified coordinate -> assigned node_id
    coord_to_id = {}
    
    for path in paths:
        parent = -1
        for i, pt in enumerate(path):
            coord_key = f"{pt[0]:.2f}_{pt[1]:.2f}_{pt[2]:.2f}"
            
            if coord_key in coord_to_id:
                # Node already exists (intersection)
                curr_id = coord_to_id[coord_key]
                if parent != -1 and parent != curr_id:
                    # Link previous to this intersecting node (this is an edge, not a new node)
                    # SWC is a tree. If a path loops back or merges, SWC strict format (tree) is violated.
                    # We will just start a new branch whose parent is curr_id, but since we are iterating,
                    # if this is not the first point, we shouldn't really have multiple parents.
                    # Actually, we can just treat the intersecting node as the parent for the next segment.
                    pass
                parent = curr_id
                continue
                
            # New Node
            curr_id = node_id
            coord_to_id[coord_key] = curr_id
            node_id += 1
            
            # Determine type and radius
            ntype, radius = 3, 1.0 # default (dendrite)
            if tree is not None:
                dist, idx = tree.query(pt)
                if dist < 5.0: # If within 5 pixels, inherit original properties
                    ntype = original_attrs[idx]['type']
                    radius = original_attrs[idx]['radius']
            
            # SWC format: id type x y z radius parent
            # Note pt is [z, y, x], output x, y, z
            swc_lines.append(f"{curr_id} {ntype} {pt[2]:.3f} {pt[1]:.3f} {pt[0]:.3f} {radius:.3f} {parent}\n")
            parent = curr_id
            
    with open(filepath, 'w') as f:
        f.writelines(swc_lines)
    print(f"Saved SWC Skeleton to {filepath}")


def color_connected_components(paths):
    """
    Identifies connected paths (unique trees) and assigns a distinct color to each tree.
    """
    import matplotlib.cm as cm
    graph = nx.Graph()
    for i, path in enumerate(paths):
        if len(path) > 0:
            # Keys based on endpoints
            p1_key = f"{path[0][0]:.2f}_{path[0][1]:.2f}_{path[0][2]:.2f}"
            p2_key = f"{path[-1][0]:.2f}_{path[-1][1]:.2f}_{path[-1][2]:.2f}"
            graph.add_node(p1_key)
            graph.add_node(p2_key)
            # networkx MultiGraph allows multiple edges between same nodes, but Graph overwrites
            # We will just append path_idx to a list
            if graph.has_edge(p1_key, p2_key):
                graph[p1_key][p2_key]['path_idxs'].append(i)
            else:
                graph.add_edge(p1_key, p2_key, path_idxs=[i])
            
    components = list(nx.connected_components(graph))
    
    base_colors = cm.tab20(np.linspace(0, 1, 20))
    colors = ['cyan'] * len(paths)
    
    for comp_idx, comp_nodes in enumerate(components):
        color = base_colors[comp_idx % 20]
        subgraph = graph.subgraph(comp_nodes)
        for u, v, data in subgraph.edges(data=True):
            for idx in data.get('path_idxs', []):
                colors[idx] = color
                
    return colors


def run_viewer(raw_path, skeletons_path, centroids_path):
    viewer = napari.Viewer(title="Unified Proofreading Viewer")
    voxel_scale = (0.5, 0.1102, 0.1102)

    raw_vol = None
    if raw_path and os.path.exists(raw_path):
        print(f"Loading raw volume: {raw_path}")
        raw_vol = tifffile.imread(raw_path, out='memmap')
        p1, p99 = np.percentile(raw_vol[::10, ::10, ::10], (1, 99.9))
        viewer.add_image(raw_vol, name='Raw Volume', scale=voxel_scale, colormap='magenta', blending='additive', contrast_limits=[p1, p99])
    else:
        print("No raw volume provided. Open viewer blank.")
    
    # State tracking
    orig_skel_pts = []
    orig_skel_attrs = []
    cw_skel_data = None
    
    # --- LOAD SKELETONS ---
    if skeletons_path and os.path.exists(skeletons_path):
        print(f"Loading Skeletons from {skeletons_path}")
        if skeletons_path.endswith('.swc'):
            paths, orig_skel_pts, orig_skel_attrs = parse_swc_skeleton(skeletons_path)
            if paths:
                colors = color_connected_components(paths)
                viewer.add_shapes(paths, shape_type='path', edge_color=colors, edge_width=2, name='Skeletons (Edges)', scale=voxel_scale)
        elif skeletons_path.endswith('.json'):
            with open(skeletons_path, 'r') as f:
                cw_skel_data = json.load(f)
            nodes = [n['coord'] for n in cw_skel_data.get('cells_0_nodes', [])]
            paths = [l['geometry'] for l in cw_skel_data.get('cells_1_linestrings', [])]
            if nodes:
                viewer.add_points(np.array(nodes), name='Skeleton (Nodes)', size=3, face_color='red', scale=voxel_scale)
            if paths:
                colors = color_connected_components(paths)
                viewer.add_shapes(paths, shape_type='path', edge_color=colors, edge_width=2, name='Skeletons (Edges)', scale=voxel_scale)

    # --- LOAD CENTROIDS ---
    cw_cent_data = None
    if centroids_path and os.path.exists(centroids_path):
        print(f"Loading Centroids from {centroids_path}")
        if centroids_path.endswith('.swc'):
            coords = []
            with open(centroids_path, 'r') as f:
                for line in f:
                    if line.startswith('#') or not line.strip(): continue
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        coords.append([float(parts[4]), float(parts[3]), float(parts[2])]) # z,y,x
            if coords:
                viewer.add_points(np.array(coords), name='Centroids', size=8, face_color='yellow', scale=voxel_scale)
        elif centroids_path.endswith('.json'):
            with open(centroids_path, 'r') as f:
                cw_cent_data = json.load(f)
            nodes = [n['coord'] for n in cw_cent_data.get('cells_0_nodes', [])]
            if nodes:
                viewer.add_points(np.array(nodes), name='Centroids', size=8, face_color='yellow', scale=voxel_scale)

    # --- INSTRUCTIONS OVERLAY ---
    viewer.text_overlay.visible = True
    viewer.text_overlay.color = 'white'
    viewer.text_overlay.text = "Unified Editor\nModify Shapes/Points and Press 'S' to Save."

    # --- SAVE LOGIC ---
    @viewer.bind_key('s')
    def save_state(viewer):
        print("Saving Proofreading Edits...")
        
        def snap_to_intensity(pt, vol, radius=4):
            z, y, x = int(round(pt[0])), int(round(pt[1])), int(round(pt[2]))
            z_min, z_max = max(0, z - radius), min(vol.shape[0], z + radius + 1)
            y_min, y_max = max(0, y - radius), min(vol.shape[1], y + radius + 1)
            x_min, x_max = max(0, x - radius), min(vol.shape[2], x + radius + 1)
            
            sub_vol = vol[z_min:z_max, y_min:y_max, x_min:x_max]
            if sub_vol.size == 0:
                return pt
                
            max_idx = np.unravel_index(np.argmax(sub_vol), sub_vol.shape)
            return [z_min + max_idx[0], y_min + max_idx[1], x_min + max_idx[2]]
        
        # Save Skeletons
        if skeletons_path:
            shapes_layer = viewer.layers['Skeletons (Edges)'] if 'Skeletons (Edges)' in viewer.layers else None
            paths_data = shapes_layer.data if shapes_layer else []
            
            nodes_layer = viewer.layers['Skeleton (Nodes)'] if 'Skeleton (Nodes)' in viewer.layers else None
            nodes_data = nodes_layer.data if nodes_layer else []
            
            # Snap geometry to local intensity maximum
            snapped_paths = []
            for p in paths_data:
                new_p = np.copy(p)
                if raw_vol is not None and len(new_p) > 0:
                    for i in range(len(new_p)):
                        new_p[i] = snap_to_intensity(new_p[i], raw_vol, radius=4)
                snapped_paths.append(new_p)
                
            snapped_nodes = []
            for n in nodes_data:
                if raw_vol is not None:
                    snapped_nodes.append(snap_to_intensity(n, raw_vol, radius=4))
                else:
                    snapped_nodes.append(n)
                
            if shapes_layer:
                shapes_layer.data = snapped_paths
                new_colors = color_connected_components(snapped_paths)
                shapes_layer.edge_color = new_colors
                shapes_layer.refresh()
            if nodes_layer:
                nodes_layer.data = np.array(snapped_nodes) if len(snapped_nodes) > 0 else np.empty((0,3))
            
            if skeletons_path.endswith('.swc'):
                save_swc_skeleton(skeletons_path, snapped_paths, orig_skel_pts, orig_skel_attrs)
            elif skeletons_path.endswith('.json') and cw_skel_data is not None:
                cw_skel_data['cells_1_linestrings'] = [
                    {"geometry": [[int(c[0]), int(c[1]), int(c[2])] for c in p]} for p in snapped_paths
                ]
                cw_skel_data['cells_0_nodes'] = [
                    {"node_id": i, "coord": [int(c[0]), int(c[1]), int(c[2])]} for i, c in enumerate(snapped_nodes)
                ]
                with open(skeletons_path, 'w') as f:
                    json.dump(cw_skel_data, f, indent=2)
                print(f"Saved CW JSON Skeleton to {skeletons_path}")

        # Save Centroids
        if centroids_path and 'Centroids' in viewer.layers:
            pts_data = viewer.layers['Centroids'].data
            if centroids_path.endswith('.swc'):
                with open(centroids_path, 'w') as f:
                    f.write("# Proofread Centroids SWC\n")
                    for i, c in enumerate(pts_data):
                        f.write(f"{i+1} 1 {c[2]:.3f} {c[1]:.3f} {c[0]:.3f} 1.0 -1\n")
                print(f"Saved Centroids SWC to {centroids_path}")
            elif centroids_path.endswith('.json') and cw_cent_data is not None:
                cw_cent_data['cells_0_nodes'] = [
                    {"node_id": i, "coord": [int(c[0]), int(c[1]), int(c[2])]} for i, c in enumerate(pts_data)
                ]
                with open(centroids_path, 'w') as f:
                    json.dump(cw_cent_data, f, indent=2)
                print(f"Saved Centroids CW JSON to {centroids_path}")

        viewer.text_overlay.text = "Saved successfully!"

    napari.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw', default=None)
    parser.add_argument('--skeletons', default=None)
    parser.add_argument('--centroids', default=None)
    args = parser.parse_args()
    
    raw = args.raw
    skel = args.skeletons
    cent = args.centroids
    
    if raw is None:
        try:
            from qtpy.QtWidgets import QApplication, QFileDialog
            app = QApplication.instance() or QApplication(sys.argv)
            
            raw, _ = QFileDialog.getOpenFileName(None, "Select Raw Volume TIFF (Required)", "", "TIFF Files (*.tif *.tiff);;All Files (*)")
            if raw:
                print(f"Selected Raw Volume: {raw}")
                skel_reply, _ = QFileDialog.getOpenFileName(None, "Select Skeletons File (Optional, Cancel to skip)", "", "Skeletons (*.swc *.json);;All Files (*)")
                if skel_reply:
                    skel = skel_reply
                    
                cent_reply, _ = QFileDialog.getOpenFileName(None, "Select Centroids File (Optional, Cancel to skip)", "", "Centroids (*.swc *.json);;All Files (*)")
                if cent_reply:
                    cent = cent_reply
            else:
                print("No raw volume selected. The viewer needs a raw volume to function properly.")
        except ImportError:
            print("qtpy not found. Please provide --raw argument to run standalone, or install qtpy/pyqt5.")
            
    if raw:
        run_viewer(raw, skel, cent)
