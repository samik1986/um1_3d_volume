import argparse
import tifffile
import scipy.ndimage as ndi
import numpy as np
import time
import os

def extract_dendrites(neurite_path, soma_path, output_path, radius_um=2.0):
    t0 = time.time()
    
    print(f"Loading neurite mask: {neurite_path}")
    neurite_vol = tifffile.imread(neurite_path)
    
    print(f"Loading soma mask: {soma_path}")
    soma_vol = tifffile.imread(soma_path)
    
    print(f"Calculating exact Euclidean distance transform for {radius_um}um physical padding... (O(N) fast)")
    # Using the exact physical resolutions as sampling rates
    soma_binary = soma_vol > 0
    distances = ndi.distance_transform_edt(~soma_binary, sampling=[0.5, 0.1102, 0.1102])
    
    # Any pixel within radius_um of a soma is considered part of the soma padding
    soma_dilated = distances <= radius_um
    
    print("Subtracting dilated somas from neurites to isolate dendrites...")
    dendrite_vol = neurite_vol.copy()
    dendrite_vol[soma_dilated] = 0
    
    print(f"Saving dendrite mask to {output_path}")
    tifffile.imwrite(output_path, dendrite_vol)
    print(f"Done in {time.time()-t0:.2f}s!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--neurite', required=True)
    parser.add_argument('--soma', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--radius_um', type=float, default=2.5, help="Dilation radius in micrometers")
    args = parser.parse_args()
    extract_dendrites(args.neurite, args.soma, args.output, args.radius_um)
