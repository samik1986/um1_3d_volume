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

def run_pipeline(input_vol, output_swc, keep_intermediates, workers):
    out_dir = os.path.dirname(os.path.abspath(output_swc))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        
    swc_base = os.path.basename(output_swc)
    name_prefix = swc_base.replace('.swc', '')
    
    # We keep soma labels as requested
    soma_labels = os.path.join(out_dir, f"{name_prefix}_soma_labels.tif")
    
    # Intermediate files
    neurite_mask = os.path.join(out_dir, f"{name_prefix}_temp_neurite_mask.tif")
    skeleton_mask = os.path.join(out_dir, f"{name_prefix}_temp_skeleton_mask.tif")
    
    t0 = time.time()
    
    # 1. Detect Somas
    if not os.path.exists(soma_labels):
        cmd = ["python", "-u", "detect_somas.py", "--input", input_vol, "--output", soma_labels, "--workers", "4"]
        run_command(cmd)
    else:
        print(f"Skipping Soma Detection, {soma_labels} exists.")
        
    # 2. Neurite Detection
    if not os.path.exists(neurite_mask):
        cmd = ["python", "-u", "process_neurites.py", "--input", input_vol, "--output", neurite_mask, "--workers", "4"]
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
    # The trace script automatically generates output_swc and output_swc_microns.swc
    if not os.path.exists(output_swc):
        cmd = ["python", "-u", "trace_and_connect_skeletons.py", "--mask", skeleton_mask, "--output", output_swc, "--gap", "15", "--sample_rate", "10"]
        run_command(cmd)
    else:
        print(f"Skipping Vectorization, {output_swc} exists.")
        
    # Cleanup Intermediates
    if not keep_intermediates:
        print("\nCleaning up intermediate masks...")
        for temp_file in [neurite_mask, skeleton_mask]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                print(f"Deleted {temp_file}")
                
    print(f"========================================================")
    print(f"FULL PIPELINE COMPLETED SUCCESSFULLY IN {time.time()-t0:.2f}s")
    print(f"Outputs generated:")
    print(f"- {soma_labels}")
    print(f"- {output_swc}")
    print(f"- {output_swc.replace('.swc', '_microns.swc')}")
    print(f"========================================================")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="End-to-End 3D Neuron Skeletonization Pipeline")
    parser.add_argument('-i', '--input', required=True, help="Path to raw 3D TIFF volume")
    parser.add_argument('-o', '--output_swc', required=True, help="Path to save the output SWC (e.g. out/neuron.swc). The _microns.swc will be generated automatically alongside it.")
    parser.add_argument('--keep_intermediates', action='store_true', help="Do not delete intermediate neurite and skeleton masks")
    parser.add_argument('--workers', type=int, default=8, help="Number of CPU workers for skeletonization")
    args = parser.parse_args()
    
    run_pipeline(args.input, args.output_swc, args.keep_intermediates, args.workers)
