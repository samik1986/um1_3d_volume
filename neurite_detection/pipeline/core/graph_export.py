import os
import json
import numpy as np
import sknw

def export_graphs(binary_skel, output_dir, scale_z, scale_y, scale_x, centroids_488=None, out_prefix=""):
    print(f"\n--- Tracing Skeletons to Graph ---")
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract topological network from the 3D boolean volume
    print("Building topological graph from boolean skeleton...")
    graph = sknw.build_sknw(binary_skel, multi=True)
    
    cw_complex_path = os.path.join(output_dir, f"{out_prefix}cw_complex.json")
    swc_path = os.path.join(output_dir, f"{out_prefix}skeletons.swc")
    cw_complex_scaled_path = os.path.join(output_dir, f"{out_prefix}cw_complex_micrometers.json")
    swc_scaled_path = os.path.join(output_dir, f"{out_prefix}skeletons_micrometers.swc")
    
    cw_nodes = []
    cw_linestrings = []
    cw_nodes_scaled = []
    cw_linestrings_scaled = []
    
    swc_lines = ["# Skeletons converted from sknw\n", "# Units: voxels\n", "# Node Types: 3=Skeleton, 2=Cell_488\n"]
    swc_lines_scaled = [f"# Skeletons converted from sknw (Scaled Z={scale_z}, Y={scale_y}, X={scale_x})\n", "# Units: micrometers\n", "# Node Types: 3=Skeleton, 2=Cell_488\n"]
    
    global_node_id = 1
    print(f"Extracting {len(graph.edges())} structural paths...")
    
    # Iterate over the sknw graph edges to construct paths
    for (s, e, k) in graph.edges(keys=True):
        pts = graph[s][e][k]['pts']
        
        parent_swc_id = -1
        
        for i in range(len(pts)):
            curr = pts[i]
            z, y, x = float(curr[0]), float(curr[1]), float(curr[2])
            z_sc, y_sc, x_sc = z * scale_z, y * scale_y, x * scale_x
            
            curr_swc_id = global_node_id
            global_node_id += 1
            
            cw_nodes.append({"node_id": curr_swc_id, "coord": [z, y, x], "type": "skeleton"})
            cw_nodes_scaled.append({"node_id": curr_swc_id, "coord": [z_sc, y_sc, x_sc], "type": "skeleton"})
            
            swc_lines.append(f"{curr_swc_id} 3 {x:.3f} {y:.3f} {z:.3f} 1.0 {parent_swc_id}\n")
            swc_lines_scaled.append(f"{curr_swc_id} 3 {x_sc:.5f} {y_sc:.5f} {z_sc:.5f} 1.0 {parent_swc_id}\n")
            
            if parent_swc_id != -1:
                pz, py, px = float(pts[i-1][0]), float(pts[i-1][1]), float(pts[i-1][2])
                pz_sc, py_sc, px_sc = pz * scale_z, py * scale_y, px * scale_x
                cw_linestrings.append({"geometry": [[pz, py, px], [z, y, x]]})
                cw_linestrings_scaled.append({"geometry": [[pz_sc, py_sc, px_sc], [z_sc, y_sc, x_sc]]})
                
            parent_swc_id = curr_swc_id

    if centroids_488 is not None:
        for c in centroids_488:
            z, y, x = float(c[0]), float(c[1]), float(c[2])
            z_sc, y_sc, x_sc = z * scale_z, y * scale_y, x * scale_x
            curr_id = global_node_id
            global_node_id += 1
            cw_nodes.append({"node_id": curr_id, "coord": [z, y, x], "type": "cell_488"})
            cw_nodes_scaled.append({"node_id": curr_id, "coord": [z_sc, y_sc, x_sc], "type": "cell_488"})
            swc_lines.append(f"{curr_id} 2 {x:.3f} {y:.3f} {z:.3f} 5.0 -1\n")
            swc_lines_scaled.append(f"{curr_id} 2 {x_sc:.5f} {y_sc:.5f} {z_sc:.5f} 5.0 -1\n")

    print("Writing CW-Complex JSON and SWC formats...")
    with open(cw_complex_path, 'w') as f:
        json.dump({"metadata": {"units": "voxels"}, "cells_0_nodes": cw_nodes, "cells_1_linestrings": cw_linestrings}, f, indent=2)
        
    with open(cw_complex_scaled_path, 'w') as f:
        json.dump({"metadata": {"units": "micrometers", "scale_factors": {"Z": scale_z, "Y": scale_y, "X": scale_x}}, "cells_0_nodes": cw_nodes_scaled, "cells_1_linestrings": cw_linestrings_scaled}, f, indent=2)
        
    with open(swc_path, 'w') as f:
        f.writelines(swc_lines)
        
    with open(swc_scaled_path, 'w') as f:
        f.writelines(swc_lines_scaled)
        
    print(f"Exported scaled & unscaled Graphs to: {output_dir}")
