"""
io_utils.py (neuron_detection)

Author: Samik Banerjee
Date: May 8, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

Memory-efficient TIFF I/O utilities for loading and extracting subvolumes.
"""

import tifffile
import os

def load_tiff_memmap(filepath):
    """Safely loads a large TIFF file as a memory-mapped numpy array."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File {filepath} not found.")
    tif = tifffile.TiffFile(filepath)
    return tif.asarray(out='memmap')

def extract_subvolume(memmap_vol, z_range, y_range, x_range):
    """Extracts a specific bounding box from the memory-mapped volume."""
    return memmap_vol[z_range[0]:z_range[1], 
                      y_range[0]:y_range[1], 
                      x_range[0]:x_range[1]].copy()
