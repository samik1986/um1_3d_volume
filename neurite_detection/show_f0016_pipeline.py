import os
import json
import numpy as np
import tifffile
from qtpy.QtWidgets import QApplication
import napari

app = QApplication.instance() or QApplication([])
viewer = napari.Viewer(ndisplay=3)

scale = (0.500, 0.1102, 0.1102)
base_dir = r"C:\Users\banerjee\Desktop\um1_3d_volume"
raw_path = os.path.join(base_dir, "NEWFP", "F0016_FP.tif")
barcode_path = os.path.join(base_dir, "NEWFP", "F0016_barcode.tif")
output_dir = os.path.join(base_dir, "NEWFP_output", "F0016_FP")

mask_path = os.path.join(output_dir, "neurite_mask.tif")
soma_path = os.path.join(output_dir, "soma_labels.tif")
cw_path = os.path.join(output_dir, "cw_complex.json")

print("Loading raw image...")
viewer.open(raw_path, name="Raw FP", colormap="gray", blending="additive", scale=scale)

print("Loading barcodes...")
try:
    # First try memmap to avoid huge RAM spike
    barcode_img = tifffile.memmap(barcode_path)
    viewer.add_image(barcode_img, name="Barcodes", colormap="green", blending="additive", scale=scale, visible=False)
except Exception as e:
    print(f"Failed to memmap barcodes: {e}. Falling back to read...")
    barcode_img = tifffile.imread(barcode_path)
    viewer.add_image(barcode_img, name="Barcodes", colormap="green", blending="additive", scale=scale, visible=False)

mask_img = None
if os.path.exists(mask_path):
    print("Loading neurite volume...")
    mask_img = tifffile.imread(mask_path)
    viewer.add_labels(mask_img, name="Neurite Volume", scale=scale, visible=False)
    
    print("Computing filtered barcodes...")
    # Convert to array to avoid modifying memmap
    filtered_barcodes = np.array(barcode_img, copy=True)
    filtered_barcodes[mask_img == 0] = 0
    viewer.add_image(filtered_barcodes, name="Filtered Barcodes", colormap="magenta", blending="additive", scale=scale, visible=False)
    
    print("Computing filtered neurites...")
    filtered_neurites = np.copy(mask_img)
    filtered_neurites[barcode_img == 0] = 0
    viewer.add_labels(filtered_neurites, name="Filtered Neurites", scale=scale, visible=False)
else:
    print("Neurite mask not found.")

soma_mask = None
if os.path.exists(soma_path):
    print("Loading soma labels...")
    soma_img = tifffile.imread(soma_path)
    viewer.add_labels(soma_img, name="Soma", scale=scale, visible=False)
    soma_mask = soma_img > 0
else:
    print("Soma labels not found.")

if os.path.exists(cw_path):
    print("Loading skeletons...")
    with open(cw_path, 'r') as f:
        cw_data = json.load(f)
    
    paths = []
    filtered_paths = []
    
    for p in cw_data.get('cells_1_linestrings', []):
        if 'geometry' in p:
            geom = p['geometry']
            paths.append(geom)
            
            # Filter skeletons: remove portions inside the soma
            if soma_mask is not None:
                subpath = []
                for pt in geom:
                    z, y, x = int(pt[0]), int(pt[1]), int(pt[2])
                    if 0 <= z < soma_mask.shape[0] and 0 <= y < soma_mask.shape[1] and 0 <= x < soma_mask.shape[2]:
                        if not soma_mask[z, y, x]:
                            subpath.append(pt)
                        else:
                            if len(subpath) >= 2:
                                filtered_paths.append(subpath)
                            subpath = []
                    else:
                        subpath.append(pt)
                if len(subpath) >= 2:
                    filtered_paths.append(subpath)
            else:
                filtered_paths.append(geom)

    if paths:
        viewer.add_shapes(paths, shape_type='path', edge_color='yellow', edge_width=2.0, name="Skeletons", scale=scale, visible=False)
    if filtered_paths:
        viewer.add_shapes(filtered_paths, shape_type='path', edge_color='cyan', edge_width=2.0, name="Filtered Skeletons", scale=scale, visible=False)
else:
    print("Skeletons not found.")

print("Starting viewer event loop...")
app.exec_()
