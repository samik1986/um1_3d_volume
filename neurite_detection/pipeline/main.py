"""
main.py (neurite_detection/pipeline)

Author: Samik Banerjee
Date: June 10, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

Main entrypoint for the Neurite Detection Pipeline.
"""

import os

import argparse
import numpy as np
from config import DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR, CHANNEL_488, PHYSICAL_SCALE
from core.cell_detection import detect_cells_488
from core.neurite_detection import detect_neurites
from core.graph_export import export_graphs
from visualization.proofreader import run_proofreader

def main():
    parser = argparse.ArgumentParser(description="Full Volume GPU Pipeline for Neurite & Soma Detection (488 Channel)")
    parser.add_argument('--input_file', type=str, default=os.path.join(DEFAULT_INPUT_DIR, CHANNEL_488), help="Full path to the 488 TIFF file")
    parser.add_argument('--output_dir', type=str, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument('--thresh_488', type=float, default=None, help="Custom threshold for 488 neurites (default: Otsu)")
    parser.add_argument('--out_prefix', type=str, default="", help="Prefix for output filenames")
    parser.add_argument('--scale_x', type=float, default=PHYSICAL_SCALE[2], help="Physical X resolution (microns)")
    parser.add_argument('--scale_y', type=float, default=PHYSICAL_SCALE[1], help="Physical Y resolution (microns)")
    parser.add_argument('--scale_z', type=float, default=PHYSICAL_SCALE[0], help="Physical Z resolution (microns)")
    parser.add_argument('--visualize', action='store_true', help="Launch Napari proofreader at the end")
    parser.add_argument('--disable_gpu', action='store_true', help="Force CPU fallback")
    args = parser.parse_args()
    
    use_gpu = not args.disable_gpu
    os.makedirs(args.output_dir, exist_ok=True)
    
    raw_488 = args.input_file
    
    if args.out_prefix:
        prefix = f"{args.out_prefix}_"
    else:
        base_name = os.path.splitext(os.path.basename(raw_488))[0]
        prefix = f"{base_name}_"
        
    c488_soma_path = os.path.join(args.output_dir, f"{prefix}centroids_488_soma.npy")
    soma_488_path = os.path.join(args.output_dir, f"{prefix}soma_mask_488.npy")
    
    print("\n====================")
    print("1. Soma Detection (488 Channel)")
    print("====================")
    c488_soma, mask488_soma = detect_cells_488(raw_488)
    np.save(c488_soma_path, c488_soma)
    if mask488_soma is not None:
        np.save(soma_488_path, mask488_soma)
        soma_masks = [mask488_soma]
    else:
        soma_masks = None
        
    print("\n====================")
    print("2. Neurite Volumetric Detection (GPU)")
    print("====================")
    neurite_mask, binary_skel = detect_neurites(raw_488, custom_thresh=args.thresh_488, soma_masks=soma_masks, use_gpu=use_gpu)
    
    neurite_path = os.path.join(args.output_dir, f"{prefix}neurite_mask_488.npy")
    np.save(neurite_path, neurite_mask)
    print(f"Saved 3D Neurite Volume to: {neurite_path}")
    
    skeleton_path = os.path.join(args.output_dir, f"{prefix}skeleton_mask_488.npy")
    np.save(skeleton_path, binary_skel)
    print(f"Saved 1-pixel 3D Skeleton Volume to: {skeleton_path}")
    
    print("\n====================")
    print("3. Graph Export (SWC & JSON)")
    print("====================")
    
    # Memory Management: Free arrays before graph export to prevent OOM
    del neurite_mask
    if 'mask488_soma' in locals() and mask488_soma is not None:
        del mask488_soma
    import gc
    gc.collect()
    
    try:
        export_graphs(binary_skel, args.output_dir, args.scale_z, args.scale_y, args.scale_x, centroids_488=c488_soma, out_prefix=prefix)
    except Exception as e:
        print(f"\n[WARNING] Graph Export failed due to memory error or topology complexity. Skipping JSON/SWC export.")
        print(f"Error details: {e}")
    
    if args.visualize:
        print("\n====================")
        print("4. Visualization & Proofreading")
        print("====================")
        run_proofreader(raw_488, soma_mask_path=soma_488_path, neurite_mask_path=neurite_path, skeleton_mask_path=skeleton_path, centroids_488_path=c488_soma_path)
        
    print("\nPipeline execution complete!")

if __name__ == "__main__":
    main()
