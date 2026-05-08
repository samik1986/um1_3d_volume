"""
process_centroids.py

Command-line application to convert a directory of SWC files (containing 2D slice centroids) 
into a 3D CW-Complex JSON format.

Usage:
    python process_centroids.py -i <input_dir> -o <output_file>

Arguments:
    -i, --input  : Path to the directory containing slice-wise SWC files.
    -o, --output : Filepath where the output CW-Complex JSON will be saved.

Example:
    python process_centroids.py -i "../a3_ch04_Swc/slices" -o "centroid_cw_complex.json"
"""

import os
import argparse
from utils import parse_swc_files, serialize_to_cw_complex

def main():
    parser = argparse.ArgumentParser(description="Convert a folder of SWC files containing cell centroids into a CW-Complex JSON.")
    parser.add_argument(
        '-i', '--input', 
        type=str, 
        required=True, 
        help="Input directory containing .swc files."
    )
    parser.add_argument(
        '-o', '--output', 
        type=str, 
        required=True, 
        help="Output filepath for the CW-Complex JSON."
    )
    
    args = parser.parse_args()
    
    input_dir = args.input
    out_file = args.output
    
    if not os.path.exists(input_dir):
        print(f"Error: Input directory {input_dir} not found.")
        return
        
    print(f"Starting processing for centroids in: {input_dir}")
    nodes_list = parse_swc_files(input_dir)
    
    if not nodes_list:
        print("No nodes were parsed. Exiting.")
        return
        
    print(f"Serializing to: {out_file}")
    serialize_to_cw_complex(nodes_list, out_file)

if __name__ == "__main__":
    main()
