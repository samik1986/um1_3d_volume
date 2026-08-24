import os
import subprocess
import time
import argparse

def run_command(cmd):
    print(f"\n========================================================")
    print(f"RUNNING: {' '.join(cmd)}")
    print(f"========================================================\n")
    start = time.time()
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Command failed with exit code {e.returncode}")
        exit(1)
    print(f"\nCompleted in {time.time()-start:.2f}s\n")

def run_pipeline(raw_vol, out_dir, workers=8):
    os.makedirs(out_dir, exist_ok=True)
    
    soma_labels = os.path.join(out_dir, "soma_labels_new.tif")
    neurite_mask = os.path.join(out_dir, "neurite_mask.tif")
    skeleton_mask = os.path.join(out_dir, "skeleton_mask_new.tif")
    swc_out = os.path.join(out_dir, "skeletons_connected_new.swc")
    
    t0 = time.time()
    
    # 1. Detect Somas
    if not os.path.exists(soma_labels):
        cmd = ["python", "-u", "detect_somas.py", "--input", raw_vol, "--output", soma_labels, "--workers", "4"]
        run_command(cmd)
    else:
        print(f"Skipping Soma Detection, {soma_labels} exists.")
        
    # 2. Neurite Detection
    if not os.path.exists(neurite_mask):
        cmd = ["python", "-u", "process_neurites.py", "--input", raw_vol, "--output", neurite_mask, "--workers", "4"]
        run_command(cmd)
    else:
        print(f"Skipping Neurite Detection, {neurite_mask} exists.")
        
    # 3. Fast Skeletonization & Soma Subtraction
    if not os.path.exists(skeleton_mask):
        cmd = ["python", "-u", "skeletonize_fast.py", "--neurite", neurite_mask, "--soma", soma_labels, "--output", skeleton_mask, "--workers", str(workers)]
        run_command(cmd)
    else:
        print(f"Skipping Skeletonization, {skeleton_mask} exists.")
        
    # 4. Vectorization and Graph Tracing
    if not os.path.exists(swc_out):
        cmd = ["python", "-u", "trace_and_connect_skeletons.py", "--mask", skeleton_mask, "--output", swc_out, "--gap", "15", "--sample_rate", "5"]
        run_command(cmd)
    else:
        print(f"Skipping Vectorization, {swc_out} exists.")
        
    print(f"========================================================")
    print(f"FULL PIPELINE COMPLETED SUCCESSFULLY IN {time.time()-t0:.2f}s")
    print(f"========================================================")
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--volume', required=True)
    parser.add_argument('--out_dir', required=True)
    parser.add_argument('--workers', type=int, default=8)
    args = parser.parse_args()
    
    run_pipeline(args.volume, args.out_dir, args.workers)
