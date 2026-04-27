import tifffile
import numpy as np
import os

def divide_tiff_into_quadrants(input_path, output_dir='quadrants'):
    """
    Divided a 3D TIFF volume into 4 spatial quadrants (2x2 grid) 
    memory-efficiently by processing slice-by-slice.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"Opening {input_path}...")
    with tifffile.TiffFile(input_path) as tif:
        # Get volume metadata
        num_slices = len(tif.pages)
        first_page = tif.pages[0]
        height, width = first_page.shape
        dtype = first_page.dtype
        
        print(f"Volume dimensions: {width}x{height}x{num_slices} [{dtype}]")
        
        # Calculate quadrant boundaries
        mid_h = height // 2
        mid_w = width // 2
        
        # Define 4 quadrants: (row_start, row_end, col_start, col_end)
        quads = [
            (0, mid_h, 0, mid_w, "Q1_top_left"),
            (0, mid_h, mid_w, width, "Q2_top_right"),
            (mid_h, height, 0, mid_w, "Q3_bottom_left"),
            (mid_h, height, mid_w, width, "Q4_bottom_right")
        ]
        
        # Initialize Writers for each quadrant
        writers = []
        for _, _, _, _, name in quads:
            out_name = os.path.join(output_dir, f"{name}.tif")
            writers.append(tifffile.TiffWriter(out_name, bigtiff=True))
            print(f"Targeting: {out_name}")

        try:
            # Process slice by slice to save RAM
            for i, page in enumerate(tif.pages):
                if i % 50 == 0:
                    print(f"Processing slice {i}/{num_slices}...")
                
                # Read single slice
                img_slice = page.asarray()
                
                # Write each quadrant
                for q_idx, (r1, r2, c1, c2, _) in enumerate(quads):
                    q_crop = img_slice[r1:r2, c1:c2]
                    writers[q_idx].write(q_crop, contiguous=True)
                    
        finally:
            # Safely close all writers
            for w in writers:
                w.close()
                
    print("\nProcessing Complete. Quadrants saved to:", os.path.abspath(output_dir))

if __name__ == "__main__":
    # Example usage for FP.tif
    input_file = "FP.tif"
    if os.path.exists(input_file):
        divide_tiff_into_quadrants(input_file)
    else:
        print(f"Error: {input_file} not found in the current directory.")
