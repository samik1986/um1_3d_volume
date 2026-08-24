import os
import time
import argparse
import tifffile
import numpy as np
from process_neurites import detect_neurites_volume
from detect_somas import detect_somas
from skeletonize_only import skeletonize_to_swc

def visualize_results(raw_volume, swc_path, skeleton_mask_path=None, soma_mask_path=None):
    print("Launching Napari for visualization...")
    try:
        import napari
    except ImportError:
        print("Napari is not installed. Skipping visualization.")
        return
        
    viewer = napari.Viewer(ndisplay=3)
    
    # Hide somas from the background raw volume if requested
    disp_volume = raw_volume.copy()
    if soma_mask_path and os.path.exists(soma_mask_path):
        soma_mask = tifffile.imread(soma_mask_path)
        disp_volume[soma_mask > 0] = 0
    
    # Add raw volume with physical scaling
    # Z=0.5, Y=0.1102, X=0.1102
    viewer.add_image(disp_volume, name='Raw Volume (No Somas)', colormap='gray', blending='additive', scale=(0.5, 0.1102, 0.1102))
    
    if skeleton_mask_path and os.path.exists(skeleton_mask_path):
        print("Loading skeleton mask for ultra-fast GPU rendering...")
        skeleton_mask = tifffile.imread(skeleton_mask_path)
        viewer.add_image(skeleton_mask, name='Skeletons', colormap='red', blending='additive', scale=(0.5, 0.1102, 0.1102))
    else:
        print("Skeleton mask not found, skipping skeleton visualization.")
        
    napari.run()

def run_pipeline_in_memory(input_tiff, output_dir, workers, no_vis=False):
    os.makedirs(output_dir, exist_ok=True)
    
    mask_path = os.path.join(output_dir, "neurite_mask.tif")
    soma_labels_path = os.path.join(output_dir, "soma_labels.tif")
    swc_path = os.path.join(output_dir, "skeletons_only.swc")
    skeleton_mask_path = os.path.join(output_dir, "skeleton_mask.tif")
    
    print(f"=== Starting In-Memory Neurite Detection Pipeline ===")
    print(f"Input: {input_tiff}")
    print(f"Output Directory: {output_dir}")
    
    # 0. Load the full volume once!
    print("\n--- Step 0: Load Volume into Memory ---")
    t0 = time.time()
    volume_array = tifffile.imread(input_tiff)
    print(f"Volume loaded in {time.time()-t0:.2f}s")
    
    if os.path.exists(swc_path) and os.path.exists(skeleton_mask_path):
        print(f"\nSkeleton SWC and Mask already exist at: {output_dir}")
        print("Skipping processing pipeline...")
        if not no_vis:
            visualize_results(volume_array, swc_path, skeleton_mask_path=skeleton_mask_path, soma_mask_path=soma_labels_path)
        else:
            print("Skipping Visualization (--no-vis).")
        return

    # 1. Neurite Detection
    if os.path.exists(mask_path):
        print(f"\n--- Step 1: Loading existing Neurite Mask ---")
        t1 = time.time()
        neurite_array = tifffile.imread(mask_path)
        print(f"Loaded existing neurite mask from disk in {time.time()-t1:.2f}s")
    else:
        print("\n--- Step 1: GPU Accelerated Neurite Detection ---")
        t1 = time.time()
        neurite_array = detect_neurites_volume(volume_array, mask_path, workers=workers)
        print(f"Step 1 Complete. Time Complexity: {time.time()-t1:.2f}s")
    
    # 2. Soma Detection
    if os.path.exists(soma_labels_path):
        print(f"\n--- Step 2: Loading existing Soma Mask ---")
        t2 = time.time()
        soma_array = tifffile.imread(soma_labels_path)
        print(f"Loaded existing soma mask from disk in {time.time()-t2:.2f}s")
    else:
        print("\n--- Step 2: GPU Accelerated Soma Detection ---")
        t2 = time.time()
        soma_array = detect_somas(volume_array, soma_labels_path, workers=workers)
        print(f"Step 2 Complete. Time Complexity: {time.time()-t2:.2f}s")
    
    # 3. Skeletonization to SWC
    print("\n--- Step 3: Skeletonization to SWC (In Memory) ---")
    t3 = time.time()
    # Apply physical scaling: Z=0.5, Y=0.1102, X=0.1102
    skeletonize_to_swc(neurite_array, soma_array, swc_path, out_skeleton_path=skeleton_mask_path, scale=(0.5, 0.1102, 0.1102))
    print(f"Step 3 Complete. Time Complexity: {time.time()-t3:.2f}s")
    
    print(f"\n=== Entire Pipeline Finished in {time.time()-t0:.2f}s ===")
    
    if not no_vis:
        visualize_results(volume_array, swc_path, skeleton_mask_path=skeleton_mask_path, soma_mask_path=soma_labels_path)
    else:
        print("\nSkipping Visualization (--no-vis).")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help="Input TIFF path")
    parser.add_argument('--outdir', default="output", help="Output directory")
    parser.add_argument('--workers', type=int, default=4, help="Number of GPU threads")
    parser.add_argument('--no-vis', action='store_true', help="Skip launching Napari")
    args = parser.parse_args()
    
    # Create a distinct output subdirectory based on the filename
    filename = os.path.basename(args.input)
    file_basename = os.path.splitext(filename)[0]
    file_outdir = os.path.join(args.outdir, file_basename)
    
    run_pipeline_in_memory(args.input, file_outdir, args.workers, args.no_vis)

if __name__ == '__main__':
    main()
