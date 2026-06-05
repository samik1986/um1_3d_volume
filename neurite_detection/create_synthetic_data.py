"""
create_synthetic_data.py (neurite_detection)

Author: Samik Banerjee
Date: June 5, 2026
GitHub: https://github.com/samik1986/um1_3d_volume
"""
import os
import json
import tifffile
import numpy as np

def create_synthetic_data():
    output_dir = "tutorial_data"
    os.makedirs(output_dir, exist_ok=True)
    
    # Dimensions
    Z, Y, X = 32, 256, 256
    
    # 1. Raw Image (Background Noise)
    raw = np.random.randint(50, 150, size=(Z, Y, X), dtype=np.uint16)
    
    # Somas
    soma1_center = (16, 64, 64)
    soma2_center = (16, 192, 192)
    radius = 12
    
    z, y, x = np.ogrid[:Z, :Y, :X]
    dist1 = np.sqrt((z - soma1_center[0])**2 + (y - soma1_center[1])**2 + (x - soma1_center[2])**2)
    dist2 = np.sqrt((z - soma2_center[0])**2 + (y - soma2_center[1])**2 + (x - soma2_center[2])**2)
    
    # Add Somas to Raw
    raw[dist1 <= radius] = 1000
    raw[dist2 <= radius] = 1000
    
    # 2. Soma Labels
    soma_labels = np.zeros_like(raw, dtype=np.uint16)
    soma_labels[dist1 <= radius] = 1
    soma_labels[dist2 <= radius] = 2
    
    # Add Neurite (A straight line from soma1 to soma2)
    num_pts = 100
    z_pts = np.linspace(soma1_center[0], soma2_center[0], num_pts)
    y_pts = np.linspace(soma1_center[1], soma2_center[1], num_pts)
    x_pts = np.linspace(soma1_center[2], soma2_center[2], num_pts)
    
    for zp, yp, xp in zip(z_pts, y_pts, x_pts):
        zp, yp, xp = int(zp), int(yp), int(xp)
        raw[max(0, zp-1):zp+2, max(0, yp-1):yp+2, max(0, xp-1):xp+2] = np.maximum(
            raw[max(0, zp-1):zp+2, max(0, yp-1):yp+2, max(0, xp-1):xp+2],
            np.random.randint(600, 900)
        )
        
    tifffile.imwrite(os.path.join(output_dir, "synthetic_raw.tif"), raw)
    tifffile.imwrite(os.path.join(output_dir, "synthetic_somas.tif"), soma_labels)
    
    # 3. Fake CW Complex (Intentionally broken)
    # The true connection is straight. We'll break it in the middle.
    n1 = [16, 64, 64]
    n2 = [16, 100, 100]
    n3 = [16, 150, 150]
    n4 = [16, 192, 192]
    
    cw_data = {
        "cells_0_nodes": [
            {"node_id": 1, "type": "endpoint", "coord": n1},
            {"node_id": 2, "type": "endpoint", "coord": n2},
            {"node_id": 3, "type": "endpoint", "coord": n3},
            {"node_id": 4, "type": "endpoint", "coord": n4}
        ],
        "cells_1_linestrings": [
            {
                "line_id": 1,
                "component_id": 1,
                "endpoints": {"source_id": 1, "target_id": 2},
                "geometry": [n1, [16, 80, 80], n2]
            },
            {
                "line_id": 2,
                "component_id": 2,
                "endpoints": {"source_id": 3, "target_id": 4},
                "geometry": [n3, [16, 170, 170], n4]
            }
        ]
    }
    with open(os.path.join(output_dir, "synthetic_cw.json"), 'w') as f:
        json.dump(cw_data, f, indent=2)
        
    # 4. Fake Centroids SWC
    # Contains soma1, misses soma2, has false positive
    with open(os.path.join(output_dir, "synthetic_centroids.swc"), 'w') as f:
        f.write("# Tutorial Centroids\n")
        # Soma 1 (Correct)
        f.write(f"1 1 {soma1_center[2]} {soma1_center[1]} {soma1_center[0]} 1.0 -1\n")
        # False Positive
        f.write(f"2 1 192 64 16 1.0 -1\n")
        
    print("Synthetic tutorial data generated in tutorial_data/")

if __name__ == "__main__":
    create_synthetic_data()
