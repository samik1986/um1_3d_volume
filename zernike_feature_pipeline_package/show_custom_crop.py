import os
import numpy as np
import tifffile
import napari
from skimage.measure import regionprops

def find_spherical_cell(labels_chunk):
    props = regionprops(labels_chunk)
    best_cell_id = None
    best_score = -1
    
    for p in props:
        if p.area < 100: # skip very small noise
            continue
        bz, by, bx, Bz, By, Bx = p.bbox
        dz = Bz - bz
        dy = By - by
        dx = Bx - bx
        
        if dz == 0 or dy == 0 or dx == 0:
            continue
            
        dims = [dz, dy, dx]
        ratio = min(dims) / max(dims)
        extent = p.extent
        
        # We can also prefer cells that are near the center of the crop
        cz, cy, cx = p.centroid
        z_mid, y_mid, x_mid = [s/2.0 for s in labels_chunk.shape]
        dist_to_center = np.sqrt((cz-z_mid)**2 + (cy-y_mid)**2 + (cx-x_mid)**2)
        
        # Weight score by distance so we prefer centered cells
        max_dist = np.sqrt(z_mid**2 + y_mid**2 + x_mid**2)
        center_weight = max(0.1, 1.0 - (dist_to_center / max_dist))
        
        score = ratio * extent * center_weight
        if score > best_score:
            best_score = score
            best_cell_id = p.label
            
    return best_cell_id, best_score

def main():
    crop_dir = r'c:\Users\banerjee\Desktop\um1_3d_volume\neuron_processing\output\custom_crops'
    ch04_path = os.path.join(crop_dir, 'crop_001_ch04.tif')
    labels_path = os.path.join(crop_dir, 'crop_001_labels.tif')
    
    if not os.path.exists(ch04_path) or not os.path.exists(labels_path):
        print("Crop files not found!")
        return
        
    print("Loading cropped volumes...")
    ch04_vol = tifffile.imread(ch04_path)
    labels_vol = tifffile.imread(labels_path)
    
    print("Finding the most spherical central cell...")
    cell_id, score = find_spherical_cell(labels_vol)
    
    if cell_id is None:
        print("No suitable cell found in the crop.")
        return
        
    print(f"Target cell ID: {cell_id} (Score: {score:.3f})")
    
    single_cell_labels = np.where(labels_vol == cell_id, cell_id, 0)
    
    print("Starting Napari...")
    viewer = napari.Viewer(title=f"Custom Crop - Spherical Cell {cell_id}")
    
    # physical voxel size in um: Z, Y, X
    voxel_scale = (0.5, 0.1102, 0.1102)
    
    viewer.add_image(ch04_vol, name='Ch04 Raw', colormap='magenta', blending='additive', scale=voxel_scale)
    viewer.add_labels(single_cell_labels, name=f'Single Cell {cell_id}', opacity=0.7, scale=voxel_scale)
    viewer.add_labels(labels_vol, name='All Cells in Crop', visible=False, opacity=0.3, scale=voxel_scale)
    
    napari.run()

if __name__ == '__main__':
    main()
