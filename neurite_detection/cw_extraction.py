"""
cw_extraction.py (neurite_detection)

Author: Samik Banerjee
Date: June 5, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

Converts the 3D binary mask into an explicit 1D topological graph representation.
"""

import json
import time
import argparse
import tifffile
import numpy as np
# pyrefly: ignore [missing-import]
import sknw
from skimage.morphology import skeletonize

def binary_to_cw_complex(binary_path, out_json_path):
    print(f"Loading binary mask: {binary_path}")
    t0 = time.time()
    # Read binary mask (values 0 and 255)
    binary_vol = tifffile.imread(binary_path) > 127
    print(f"Mask loaded in {time.time()-t0:.2f}s")
    
    print("Skeletonizing 3D volume (Time Complexity: O(N) where N=voxels)...")
    t1 = time.time()
    skeleton = skeletonize(binary_vol)
    print(f"Skeletonization complete in {time.time()-t1:.2f}s")
    
    print("Extracting graph using sknw (Time Complexity: O(S) where S=skeleton points)...")
    t2 = time.time()
    graph = sknw.build_sknw(skeleton)
    print(f"Graph extraction complete in {time.time()-t2:.2f}s")
    
    print("Converting to CW Complex Spec...")
    nodes_list = []
    lines_list = []
    
    # Process 0-cells
    for node_id, data in graph.nodes(data=True):
        z, y, x = data['o']
        node_type = "boundary" if graph.degree(node_id) == 1 else "junction"
        nodes_list.append({
            "node_id": int(node_id),
            "type": node_type,
            "coord": [int(z), int(y), int(x)]
        })
        
    # Process 1-cells
    line_id = 1
    for u, v, data in graph.edges(data=True):
        coords = data.get('pts', [])
        if len(coords) == 0:
            coords = [graph.nodes[u]['o'], graph.nodes[v]['o']]
            
        geom = [[int(pt[0]), int(pt[1]), int(pt[2])] for pt in coords]
        
        # Calculate local radius/width (simplified to constant here, but can be extracted using distance transform)
        # Note: True distance transform would be O(N).
        # We append a placeholder radius array mapping the skeleton.
        radius = [1.0] * len(geom)
        
        u_type = "boundary" if graph.degree(u) == 1 else "junction"
        v_type = "boundary" if graph.degree(v) == 1 else "junction"
        
        lines_list.append({
            "line_id": line_id,
            "endpoints": {"source_id": int(u), "target_id": int(v)},
            "geometry": geom,
            "forest_relation": {"connects": [u_type, v_type]},
            "radius": radius
        })
        line_id += 1
        
    cw_complex = {
        "network_type": "1D/2D/3D CW Complex Forest",
        "cells_0_nodes": nodes_list,
        "cells_1_linestrings": lines_list,
        "cells_2_surfaces": [],
        "cells_3_volumes": []
    }
    
    print(f"Saving CW-Complex to {out_json_path}...")
    with open(out_json_path, 'w') as f:
        json.dump(cw_complex, f, indent=2)
        
    print(f"CW extraction complete. Time: {time.time()-t2:.2f}s")
    return out_json_path

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help="Input Binary TIFF")
    parser.add_argument('--output', required=True, help="Output CW Complex JSON")
    args = parser.parse_args()
    binary_to_cw_complex(args.input, args.output)
