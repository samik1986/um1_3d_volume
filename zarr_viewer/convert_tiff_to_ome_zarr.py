"""
convert_tiff_to_ome_zarr.py (zarr_viewer)

Author: Samik Banerjee
Date: May 8, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

Converts raw TIFF volumes into multiscale OME-Zarr format for efficient web-based 3D viewing.
"""

import numpy as np
import tifffile
import zarr
from numcodecs import Zlib
import json
import os
import shutil

tiff_path = '../docker_cell_detection/F0200_multichannel_cmle_ch04.tif'
swc_path = '../docker_cell_detection/centroids_DAPI.swc'
zarr_path = 'volume_final.zarr'
centroids_json = 'centroids.json'

if os.path.exists(zarr_path):
    shutil.rmtree(zarr_path)

print(f"Loading TIFF...")
data = tifffile.imread(tiff_path)
v_max = np.percentile(data, 99.9)
v_min = data.min()
diff = v_max - v_min

print("Normalizing to uint8 (slice-by-slice)...")
data_scaled = np.zeros(data.shape, dtype=np.uint8)
for i in range(data.shape[0]):
    data_scaled[i] = np.clip((data[i].astype(np.float32) - v_min) / diff * 255, 0, 255).astype(np.uint8)

data_5d = data_scaled[np.newaxis, np.newaxis, ...]

# Initialize Zarr Group
store = zarr.storage.LocalStore(zarr_path)
root = zarr.group(store=store, zarr_format=2)

compressor = Zlib(level=1)
chunks = (1, 1, 32, 256, 256)

datasets = []

current_data = data_5d
for i in range(5):
    name = f"s{i}"
    print(f"Writing {name} ({current_data.shape})...")
    
    ds = root.create_dataset(
        name, 
        shape=current_data.shape,
        dtype=current_data.dtype,
        chunks=chunks, 
        compressor=compressor
    )
    ds[:] = current_data
    
    s = 2**i
    datasets.append({
        "path": name,
        "coordinateTransformations": [{
            "type": "scale",
            "scale": [1.0, 1.0, 1.0, float(s), float(s)]
        }]
    })
    
    if i < 4:
        current_data = current_data[:, :, :, ::2, ::2]

# Write OME-Zarr metadata
multiscales = [{
    "version": "0.4",
    "name": "/",
    "axes": [
        {"name": "t", "type": "time"},
        {"name": "c", "type": "channel"},
        {"name": "z", "type": "space"},
        {"name": "y", "type": "space"},
        {"name": "x", "type": "space"}
    ],
    "datasets": datasets,
    "type": "gaussian"
}]

root.attrs["multiscales"] = multiscales
print("\nSUCCESS! Multiscales generated.")
