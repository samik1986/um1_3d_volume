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
