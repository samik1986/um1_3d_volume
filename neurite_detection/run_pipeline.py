"""
run_pipeline.py (neurite_detection)

Author: Samik Banerjee
Date: June 5, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

Master execution script orchestrating the GPU-accelerated neurite detection pipeline.
"""

import os
import argparse
import subprocess
import time

def run_pipeline(input_tiff, output_dir, workers, no_vis=False):
    os.makedirs(output_dir, exist_ok=True)
    
    mask_path = os.path.join(output_dir, "neurite_mask.tif")
    cw_path = os.path.join(output_dir, "cw_complex.json")
    
    print(f"=== Starting Neurite Detection Pipeline ===")
    print(f"Input: {input_tiff}")
    print(f"Output Directory: {output_dir}")
    
    # 1. Neurite Detection
    print("\n--- Step 1: GPU Accelerated Neurite Detection ---")
    t0 = time.time()
    cmd1 = ["python", "process_neurites.py", "--input", input_tiff, "--output", mask_path]
    subprocess.run(cmd1, check=True)
    t1 = time.time()
    print(f"Step 1 Complete. Time Complexity: {t1-t0:.2f}s")
    
    # 2. Soma Detection
    print("\n--- Step 2: GPU Accelerated Soma Detection ---")
    soma_labels_path = os.path.join(output_dir, "soma_labels.tif")
    cmd2 = ["python", "detect_somas.py", "--input", input_tiff, "--output", soma_labels_path]
    subprocess.run(cmd2, check=True)
    t2 = time.time()
    print(f"Step 2 Complete. Time Complexity: {t2-t1:.2f}s")
    
    # 3. CW Complex Extraction and Component Mapping
    print("\n--- Step 3: Skeletonization & CW Extraction ---")
    cmd3 = ["python", "cw_extraction.py", "--input", mask_path, "--output", cw_path, "--somas", soma_labels_path]
    subprocess.run(cmd3, check=True)
    t3 = time.time()
    print(f"Step 3 Complete. Time Complexity: {t3-t2:.2f}s")
    
    # 4. Viewer Launch
    if not no_vis:
        print("\n--- Step 4: Launching Napari Proofreading Viewer ---")
        cmd4 = ["python", "viewer.py", "--raw", input_tiff, "--cw", cw_path, "--mask", mask_path, "--somas", soma_labels_path]
        subprocess.run(cmd4)
    else:
        print("\n--- Step 4: Skipping Napari Viewer (--no-vis flag passed) ---")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default=r"c:\Users\banerjee\Desktop\um1_3d_volume\B3Well7_1_AN_20260529_233255_Area1_round0_20260529_233740_488_F0044_cmle.tif", help="Input TIFF path")
    parser.add_argument('--outdir', default="output", help="Output directory")
    parser.add_argument('--workers', type=int, default=4, help="Number of GPU threads")
    parser.add_argument('--no-vis', action='store_true', help="Skip launching Napari")
    args = parser.parse_args()
    
    run_pipeline(args.input, args.outdir, args.workers, args.no_vis)
