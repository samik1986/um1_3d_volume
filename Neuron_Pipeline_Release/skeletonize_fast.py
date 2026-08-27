"""
skeletonize_fast.py (neurite_detection)

Author: Samik Banerjee
Date: June 5, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

Multi-processed 3D Medial Axis Transform skeletonization.
"""
import argparse
import tifffile
import scipy.ndimage as ndi
import numpy as np
import time
from skimage.morphology import skeletonize
from concurrent.futures import ProcessPoolExecutor, as_completed

def process_chunk(args):
    z_start, z_end, y_start, y_end, x_start, x_end, overlap, chunk_data = args
    # Skeletonize the chunk
    skel_chunk = skeletonize(chunk_data)
    
    # Remove overlap regions before returning
    if y_start != 0:
        skel_chunk = skel_chunk[:, overlap:]
    if y_end != 0: # 0 indicates it was the last chunk
        skel_chunk = skel_chunk[:, :-overlap]
    if x_start != 0:
        skel_chunk = skel_chunk[:, :, overlap:]
    if x_end != 0:
        skel_chunk = skel_chunk[:, :, :-overlap]
        
    return z_start, z_end, y_start, y_end, x_start, x_end, skel_chunk

def skeletonize_fast(neurite_path, soma_path, output_path, workers=8, overlap=32):
    t0 = time.time()
    
    print(f"Loading neurite mask: {neurite_path}")
    neurite_vol = tifffile.imread(neurite_path)
    
    print(f"Loading soma mask: {soma_path}")
    soma_vol = tifffile.imread(soma_path)
    soma_binary = soma_vol > 0
    
    print("Dilating soma mask to create exclusion zone (CPU Boolean, Memory-Safe)...")
    # 2.5um padding is roughly ~5 pixels in Z (0.5um) and ~22 pixels in XY (0.11um)
    struct = ndi.generate_binary_structure(3, 1)
    # Using iterations=22 to approximate the 2.5um physical padding in high-res XY
    # Since it's boolean, this avoids the massive 22GB memory spike of EDT!
    soma_dilated = ndi.binary_dilation(soma_binary, structure=struct, iterations=22)
    
    print("Subtracting dilated somas to strictly isolate dendrites and axons...")
    dendrite_vol = (neurite_vol > 0) & (~soma_dilated)
    
    # Free up memory
    del neurite_vol, soma_vol, soma_binary, soma_dilated
    
    print("Generating Medial Axis Transform (Skeletonization)...")
    print(f"Using ProcessPoolExecutor with {workers} parallel CPU chunks to slash computation time!")
    
    depth, height, width = dendrite_vol.shape
    skel_vol = np.zeros((depth, height, width), dtype=np.uint8)
    
    # We chunk primarily in Y and X to parallelize
    chunks_y = 4
    chunks_x = 4
    
    y_step = height // chunks_y
    x_step = width // chunks_x
    
    tasks = []
    
    # Prepare chunks
    for i in range(chunks_y):
        for j in range(chunks_x):
            ys = i * y_step
            ye = (i + 1) * y_step if i != chunks_y - 1 else height
            xs = j * x_step
            xe = (j + 1) * x_step if j != chunks_x - 1 else width
            
            # Add overlap
            ys_pad = max(0, ys - overlap)
            ye_pad = min(height, ye + overlap)
            xs_pad = max(0, xs - overlap)
            xe_pad = min(width, xe + overlap)
            
            chunk_data = dendrite_vol[:, ys_pad:ye_pad, xs_pad:xe_pad]
            
            # Flags for cropping overlap
            ys_flag = ys if ys > 0 else 0
            ye_flag = ye if ye < height else 0
            xs_flag = xs if xs > 0 else 0
            xe_flag = xe if xe < width else 0
            
            tasks.append((0, depth, ys_flag, ye_flag, xs_flag, xe_flag, overlap, chunk_data))
            
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_chunk, t): t for t in tasks}
        
        count = 0
        for future in as_completed(futures):
            count += 1
            z_s, z_e, y_s, y_e, x_s, x_e, skel_chunk = future.result()
            
            y_end_idx = y_e if y_e != 0 else height
            x_end_idx = x_e if x_e != 0 else width
            
            skel_vol[:, y_s:y_end_idx, x_s:x_end_idx] = skel_chunk * 255
            print(f"Completed Medial Axis chunk {count}/{len(tasks)}")
            
    print(f"Saving parallel skeleton mask to {output_path}")
    tifffile.imwrite(output_path, skel_vol)
    
    print(f"Medial Axis Transform complete in {time.time()-t0:.2f}s!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--neurite', required=True)
    parser.add_argument('--soma', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--workers', type=int, default=8)
    
    args = parser.parse_args()
    skeletonize_fast(args.neurite, args.soma, args.output, args.workers)
