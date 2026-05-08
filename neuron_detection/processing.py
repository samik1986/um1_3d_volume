"""
processing.py (neuron_detection)

Author: Samik Banerjee
Date: May 8, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

Core image processing logic including Frangi filters, thresholding, and skeletonization.
"""

import numpy as np
from skimage.filters import frangi
from skimage.morphology import skeletonize
from skimage import exposure
import time

def preprocess_volume(subvolume, in_range=(0, 500)):
    """Normalizes the volume intensity to [0, 1] range."""
    subvol_float = subvolume.astype(np.float32)
    return exposure.rescale_intensity(subvol_float, in_range=in_range, out_range=(0, 1))

def apply_frangi_3d(subvolume, sigmas=[1, 2, 4]):
    """Applies a multi-scale 3D Frangi vesselness filter."""
    start_time = time.time()
    vesselness = frangi(subvolume, sigmas=sigmas, black_ridges=False)
    print(f"  -> Frangi computation finished in {time.time() - start_time:.2f} seconds.")
    return vesselness

def extract_skeleton(vesselness, percentile=99):
    """Thresholds the vesselness map and extracts a 1-pixel wide skeleton."""
    thresh = np.percentile(vesselness, percentile)
    binary_neurons = vesselness > thresh
    skeleton = skeletonize(binary_neurons)
    return skeleton

def process_subvolume_to_graph(subvol, global_offset=(0, 0, 0)):
    """Runs the full pipeline on a subvolume and extracts the networkx graph."""
    import sknw
    
    # 1. Preprocess
    subvol_norm = preprocess_volume(subvol)
    # 2. Frangi (only scale 1 to speed up subvolume processing, can be adjusted)
    vesselness = apply_frangi_3d(subvol_norm, sigmas=[1, 2])
    # 3. Skeletonize
    skeleton = extract_skeleton(vesselness, percentile=99)
    # 4. Extract Graph
    graph = sknw.build_sknw(skeleton, multi=True)
    
    # 5. Apply global offset so graph nodes sit in the right absolute position
    z_off, y_off, x_off = global_offset
    for n, data in graph.nodes(data=True):
        oz, oy, ox = data['o']
        data['o'] = np.array([oz + z_off, oy + y_off, ox + x_off])
        
    for u, v, key, data in graph.edges(keys=True, data=True):
        if 'pts' in data:
            # pts is usually a numpy array shape (N, 3)
            data['pts'] = data['pts'] + np.array([z_off, y_off, x_off])
            
    return graph
