import csv
import argparse
import subprocess
import os

def main():
    parser = argparse.ArgumentParser(description="Batch process multiple volumes from a CSV file using the pipeline.")
    parser.add_argument('csv_file', help="Path to the CSV file (must have 'input' and 'output' columns as headers)")
    parser.add_argument('--keep_intermediates', action='store_true', help="Keep intermediate mask files for debugging")
    parser.add_argument('--res_x', type=float, default=0.1102, help="X resolution in microns/pixel")
    parser.add_argument('--res_y', type=float, default=0.1102, help="Y resolution in microns/pixel")
    parser.add_argument('--res_z', type=float, default=0.5, help="Z resolution in microns/pixel")
    args = parser.parse_args()

    if not os.path.exists(args.csv_file):
        print(f"Error: CSV file '{args.csv_file}' not found.")
        return

    with open(args.csv_file, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        
        if not reader.fieldnames or 'input' not in reader.fieldnames or 'output' not in reader.fieldnames:
            print(f"Error: CSV file '{args.csv_file}' must contain 'input' and 'output' headers. Found: {reader.fieldnames}")
            return

        for row_idx, row in enumerate(reader, start=1):
            input_vol = row['input'].strip()
            output_swc = row['output'].strip()

            if not input_vol or not output_swc:
                print(f"Skipping row {row_idx}: Missing input or output path.")
                continue

            print(f"\n========================================================")
            print(f"BATCH FILE [{row_idx}]: {input_vol} -> {output_swc}")
            print(f"========================================================")
            
            cmd = [
                "python", "-u", "extract_skeletons.py", 
                "-i", input_vol, 
                "-o", output_swc,
                "--res_x", str(args.res_x),
                "--res_y", str(args.res_y),
                "--res_z", str(args.res_z)
            ]
            if args.keep_intermediates:
                cmd.append("--keep_intermediates")
            
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError:
                print(f"\nERROR processing {input_vol}. Skipping to next file in CSV...")
                continue
                
    print("\nBatch processing fully completed!")

if __name__ == '__main__':
    main()
