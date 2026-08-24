import argparse
import tifffile
import scipy.ndimage as ndi
import numpy as np
import time

def fast_soma_extract(mask_path, output_path, radius_um=2.5):
    t0 = time.time()
    
    print(f"Loading neurite mask: {mask_path}")
    mask = tifffile.imread(mask_path)
    
    print(f"Step 1: O(N) Exact Physical Erosion (radius={radius_um}um)...")
    # distance_transform_edt computes distance from each foreground pixel to the nearest background
    dist_in = ndi.distance_transform_edt(mask > 0, sampling=[0.5, 0.1102, 0.1102])
    
    # Anything deep enough inside is a thick structure (the core of a soma)
    soma_cores = dist_in >= radius_um
    
    print(f"Step 2: O(N) Exact Physical Dilation to restore soma shape...")
    # distance_transform_edt computes distance from background to the nearest foreground (core)
    dist_out = ndi.distance_transform_edt(~soma_cores, sampling=[0.5, 0.1102, 0.1102])
    
    # Expand the cores back out, but strictly bounded by the original mask shape
    somas_binary = (dist_out <= radius_um) & (mask > 0)
    
    print("Labeling connected somas...")
    labels_out, num_features = ndi.label(somas_binary)
    print(f"Found {num_features} raw soma candidates.")
    
    print("Filtering tiny speckles...")
    from skimage.measure import regionprops
    props = regionprops(labels_out)
    label_map = np.zeros(num_features + 1, dtype=np.uint16)
    new_label = 1
    for p in props:
        # A small volume filter just to remove tiny branches that got detached
        if p.area >= 2000:
            label_map[p.label] = new_label
            new_label += 1
            
    labels_out = label_map[labels_out]
    print(f"Filtered down to {new_label - 1} true somas.")
    
    print(f"Saving to {output_path}...")
    tifffile.imwrite(output_path, labels_out)
    print(f"Completed ultra-fast extraction in {time.time()-t0:.2f}s!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Ultra-fast morphological soma extraction from binary mask using Euclidean distance transforms.")
    parser.add_argument('--mask', required=True, help="Path to the binary neurite mask")
    parser.add_argument('--output', required=True, help="Output path for the soma labels")
    parser.add_argument('--radius_um', type=float, default=2.5, help="Radius threshold in micrometers to separate somas from dendrites")
    args = parser.parse_args()
    fast_soma_extract(args.mask, args.output, args.radius_um)
