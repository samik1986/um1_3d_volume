"""
cw_extraction.py (neurite_detection)

Author: Samik Banerjee
Date: June 5, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

Converts the 3D binary mask into an explicit 1D topological graph representation.
Includes Cell_2 and Cell_3 vectorization.
"""

import json
import time
import math
import os
import argparse
import tifffile
import numpy as np
import scipy.ndimage
import networkx as nx
# pyrefly: ignore [missing-import]
import sknw
from skimage.morphology import skeletonize

def binary_to_cw_complex(binary_path, out_json_path, soma_labels_path=None):
    print(f"Loading binary mask: {binary_path}")
    t0 = time.time()
    binary_vol = tifffile.imread(binary_path) > 127
    print(f"Mask loaded in {time.time()-t0:.2f}s")
    
    somas_vol = None
    if soma_labels_path and os.path.exists(soma_labels_path):
        print(f"Loading soma labels: {soma_labels_path}")
        somas_vol = tifffile.imread(soma_labels_path)
        print("Subtracting soma volumes from neurite mask...")
        binary_vol[somas_vol > 0] = False
    
    print("Skeletonizing 3D volume...")
    t1 = time.time()
    skeleton = skeletonize(binary_vol)
    print(f"Skeletonization complete in {time.time()-t1:.2f}s")
    
    print("Extracting graph using sknw...")
    t2 = time.time()
    graph = sknw.build_sknw(skeleton)
    print(f"Graph extraction complete in {time.time()-t2:.2f}s")
    
    # --- Map Components to Somas ---
    print("Mapping connected components to somas...")
    components = list(nx.connected_components(graph))
    node_to_component_id = {}
    
    orphan_id_counter = -1 # Negative IDs for orphan neurites
    
    for comp in components:
        comp_soma_ids = []
        if somas_vol is not None:
            for node_id in comp:
                # To map the carved-out skeleton, we check the neighborhood of the node
                z, y, x = graph.nodes[node_id]['o']
                z, y, x = int(z), int(y), int(x)
                
                # Check a 5x5x5 neighborhood to find the touching soma
                z_s = max(0, z - 2)
                z_e = min(somas_vol.shape[0], z + 3)
                y_s = max(0, y - 2)
                y_e = min(somas_vol.shape[1], y + 3)
                x_s = max(0, x - 2)
                x_e = min(somas_vol.shape[2], x + 3)
                
                neighborhood = somas_vol[z_s:z_e, y_s:y_e, x_s:x_e]
                unique_somas_in_nhood = np.unique(neighborhood)
                for s_id in unique_somas_in_nhood:
                    if s_id > 0:
                        comp_soma_ids.append(s_id)
        
        if len(comp_soma_ids) > 0:
            # Assign the most frequent soma ID touched by this component
            assigned_id = max(set(comp_soma_ids), key=comp_soma_ids.count)
        else:
            assigned_id = orphan_id_counter
            orphan_id_counter -= 1
            
        for node_id in comp:
            node_to_component_id[node_id] = int(assigned_id)

    # --- Convert to CW Complex Spec ---
    print("Converting to CW Complex Spec...")
    nodes_list = []
    lines_list = []
    surfaces_list = []
    volumes_list = []
    
    # Process 0-cells
    for node_id, data in graph.nodes(data=True):
        z, y, x = data['o']
        node_type = "boundary" if graph.degree(node_id) == 1 else "junction"
        nodes_list.append({
            "node_id": int(node_id),
            "type": node_type,
            "coord": [float(z), float(y), float(x)]
        })
        
    # Process 1-cells, 2-cells, 3-cells
    line_id = 1
    for u, v, data in graph.edges(data=True):
        coords = data.get('pts', [])
        if len(coords) == 0:
            coords = [graph.nodes[u]['o'], graph.nodes[v]['o']]
            
        geom = [[float(pt[0]), float(pt[1]), float(pt[2])] for pt in coords]
        radius = [1.0] * len(geom) # Simple uniform radius for now
        
        u_type = "boundary" if graph.degree(u) == 1 else "junction"
        v_type = "boundary" if graph.degree(v) == 1 else "junction"
        
        lines_list.append({
            "line_id": line_id,
            "component_id": node_to_component_id.get(u, -999),
            "endpoints": {"source_id": int(u), "target_id": int(v)},
            "geometry": geom,
            "forest_relation": {"connects": [u_type, v_type]},
            "radius": radius
        })
        
        # Calculate vectorized 2-cells and 3-cells
        # Cell_2_surfaces (cylinder bounding voxels or mesh - here we output simple start/end tube specs)
        # We will generate a very simple tubular boundary box mapping
        # Cell_3_volumes (Volume = length * pi * r^2)
        length = data.get('weight', len(coords))
        vol = length * math.pi * (1.0 ** 2)
        
        surfaces_list.append({
            "surface_id": line_id,
            "parent_line_id": line_id,
            "geometry": {
                "type": "tube",
                "path": geom,
                "radii": radius
            }
        })
        
        volumes_list.append({
            "volume_id": line_id,
            "parent_line_id": line_id,
            "volume_voxels": int(vol)
        })
        
        line_id += 1
        
    # Add Somas to CW Complex
    if somas_vol is not None:
        print("Extracting 3D volume boundaries for somas...")
        soma_slices = scipy.ndimage.find_objects(somas_vol)
        for s_id, s_slice in enumerate(soma_slices, start=1):
            if s_slice is None: continue
            
            z_s, z_e = s_slice[0].start, s_slice[0].stop
            y_s, y_e = s_slice[1].start, s_slice[1].stop
            x_s, x_e = s_slice[2].start, s_slice[2].stop
            
            vol_voxels = int(np.sum(somas_vol[s_slice] == s_id))
            
            soma_surface_id = 1000000 + s_id
            surfaces_list.append({
                "surface_id": soma_surface_id,
                "soma_id": s_id,
                "geometry": {
                    "type": "bounding_box",
                    "bounds": [z_s, z_e, y_s, y_e, x_s, x_e]
                }
            })
            
            soma_volume_id = 1000000 + s_id
            volumes_list.append({
                "volume_id": soma_volume_id,
                "soma_id": s_id,
                "boundary_surface_id": soma_surface_id,
                "volume_voxels": vol_voxels
            })
        
    cw_complex = {
        "network_type": "1D/2D/3D CW Complex Forest",
        "cells_0_nodes": nodes_list,
        "cells_1_linestrings": lines_list,
        "cells_2_surfaces": surfaces_list,
        "cells_3_volumes": volumes_list
    }
    
    print(f"Saving CW-Complex to {out_json_path}...")
    with open(out_json_path, 'w') as f:
        json.dump(cw_complex, f, indent=2)
        
    print(f"CW extraction complete.")
    return out_json_path

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help="Input Binary TIFF")
    parser.add_argument('--output', required=True, help="Output CW Complex JSON")
    parser.add_argument('--somas', help="Input Soma Labels TIFF")
    args = parser.parse_args()
    binary_to_cw_complex(args.input, args.output, args.somas)
