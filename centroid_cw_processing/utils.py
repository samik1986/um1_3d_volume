"""
utils.py

Author: Samik Banerjee
Date: May 8, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

Helper functions for the centroid_cw_processing module. 
Contains logic for:
1. Parsing individual SWC files to extract centroid coordinates.
2. Building a list of nodes with proper integer 3D coordinates.
3. Serializing the dataset into a standard 1D CW-Complex JSON structure.
"""

import os
import glob
import pandas as pd
import json

def parse_slice_num(filename):
    """
    Extracts the integer slice number from the filename.
    Example: A3_ch04_slice0001.swc -> 1
    """
    base = os.path.basename(filename)
    num_str = base.replace('A3_ch04_slice', '').replace('.swc', '')
    try:
        return int(num_str)
    except ValueError:
        print(f"Warning: Could not parse slice number from {filename}. Defaulting to 0.")
        return 0

def parse_swc_files(input_dir):
    """
    Parses all SWC files in the input directory and returns a list of nodes.
    """
    swc_files = glob.glob(os.path.join(input_dir, '*.swc'))
    print(f"Found {len(swc_files)} SWC files in {input_dir}.")
    
    nodes_list = []
    global_node_id = 1
    
    for f in sorted(swc_files):
        z_val = parse_slice_num(f)
        try:
            # Read SWC format: id type x y z r pid
            df = pd.read_csv(f, sep=' ', comment='#', header=None,
                             names=['id', 'type', 'x', 'y', 'z', 'r', 'pid'])
                             
            for _, row in df.iterrows():
                # Append node according to CW-Complex specification
                # Z coordinate is precisely the integer slice number
                nodes_list.append({
                    "node_id": global_node_id,
                    "type": "boundary", # Centroids are isolated points
                    "coord": [int(z_val), int(round(row['y'])), int(round(row['x']))]
                })
                global_node_id += 1
                
        except pd.errors.EmptyDataError:
            print(f"Warning: {os.path.basename(f)} is empty.")
        except Exception as e:
            print(f"Error reading {os.path.basename(f)}: {e}")
            
    return nodes_list

def serialize_to_cw_complex(nodes_list, out_file):
    """
    Serializes the list of nodes to a CW Complex JSON file.
    """
    cw_complex = {
        "metadata": {
            "description": "Header detailing the keys and values in this JSON file.",
            "network_type": "Type of network graph, e.g., '1D CW Complex Forest'.",
            "cells_0_nodes": "List of 0-cells (vertices/nodes) in the graph.",
            "node_id": "Unique integer identifier for each node.",
            "type": "Node classification (e.g., 'boundary' for isolated centroids/endpoints).",
            "coord": "3D spatial coordinates as [Z, Y, X]. Z is the slice number, Y and X are pixel coordinates.",
            "cells_1_linestrings": "List of 1-cells (edges/linestrings) connecting the nodes. Empty for a pure centroid collection."
        },
        "network_type": "1D CW Complex Forest",
        "cells_0_nodes": nodes_list,
        "cells_1_linestrings": [] # No lines, only centroids
    }
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)
    
    with open(out_file, 'w') as f:
        json.dump(cw_complex, f, indent=2)
        
    print(f"Successfully wrote {len(nodes_list)} nodes to {out_file}")
