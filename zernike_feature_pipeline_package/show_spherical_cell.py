import numpy as np
import tifffile
import napari
from skimage.measure import regionprops

def find_spherical_cell(labels_chunk):
    props = regionprops(labels_chunk)
    best_cell_id = None
    best_score = -1
    best_bbox = None
    
    for p in props:
        if p.area < 500: # skip very small noise
            continue
        # bounding box: (min_z, min_y, min_x, max_z, max_y, max_x)
        bz, by, bx, Bz, By, Bx = p.bbox
        dz = Bz - bz
        dy = By - by
        dx = Bx - bx
        
        if dz == 0 or dy == 0 or dx == 0:
            continue
            
        # 3D bounding box shape ratio
        dims = [dz, dy, dx]
        ratio = min(dims) / max(dims)
        
        # Extent = volume / bbox_volume
        extent = p.extent
        
        # A sphere has extent ~0.52 and ratio ~1.0
        score = ratio * extent
        if score > best_score:
            best_score = score
            best_cell_id = p.label
            best_bbox = p.bbox
            
    return best_cell_id, best_bbox, best_score

def main():
    labels_path = r'c:\Users\banerjee\Desktop\um1_3d_volume\neuron_processing\output\dapi_cell_labels.tif'
    ch04_path = r'C:\Users\banerjee\Desktop\um1_3d_volume\docker_cell_detection\F0200_multichannel_cmle_ch04.tif'
    
    print("Loading labels memmap...")
    labels_vol = tifffile.memmap(labels_path)
    
    # Extract a central chunk to find a cell
    print("Extracting central chunk for analysis...")
    z_mid, y_mid, x_mid = [s // 2 for s in labels_vol.shape]
    z_span, y_span, x_span = 50, 400, 400
    
    z0, z1 = max(0, z_mid - z_span), min(labels_vol.shape[0], z_mid + z_span)
    y0, y1 = max(0, y_mid - y_span), min(labels_vol.shape[1], y_mid + y_span)
    x0, x1 = max(0, x_mid - x_span), min(labels_vol.shape[2], x_mid + x_span)
    
    labels_chunk = labels_vol[z0:z1, y0:y1, x0:x1].copy()
    
    print("Finding the most spherical cell in chunk...")
    cell_id, bbox, score = find_spherical_cell(labels_chunk)
    if cell_id is None:
        print("No suitable cell found.")
        return
        
    print(f"Found highly spherical cell ID: {cell_id} (Score: {score:.3f})")
    
    # Map bbox back to global coordinates
    bz, by, bx, Bz, By, Bx = bbox
    gc_z = z0 + (bz + Bz) // 2
    gc_y = y0 + (by + By) // 2
    gc_x = x0 + (bx + Bx) // 2
    
    # Define a subvolume around this cell to extract
    sz, sy, sx = 30, 100, 100
    sub_z0, sub_z1 = max(0, gc_z - sz), min(labels_vol.shape[0], gc_z + sz)
    sub_y0, sub_y1 = max(0, gc_y - sy), min(labels_vol.shape[1], gc_y + sy)
    sub_x0, sub_x1 = max(0, gc_x - sx), min(labels_vol.shape[2], gc_x + sx)
    
    print(f"Extracting subvolumes at Z:{sub_z0}-{sub_z1}, Y:{sub_y0}-{sub_y1}, X:{sub_x0}-{sub_x1}...")
    
    # Extract labels
    labels_subvol = labels_vol[sub_z0:sub_z1, sub_y0:sub_y1, sub_x0:sub_x1].copy()
    single_cell_labels = np.where(labels_subvol == cell_id, cell_id, 0)
    
    # Extract ch04
    print("Loading ch04 subvolume...")
    # Attempt memory efficient read using key slice
    try:
        ch04_slices = tifffile.imread(ch04_path, key=range(sub_z0, sub_z1))
        ch04_subvol = ch04_slices[:, sub_y0:sub_y1, sub_x0:sub_x1].copy()
    except Exception as e:
        print(f"Slice read failed ({e}), loading full volume...")
        ch04_full = tifffile.imread(ch04_path)
        ch04_subvol = ch04_full[sub_z0:sub_z1, sub_y0:sub_y1, sub_x0:sub_x1].copy()
        del ch04_full
        
    print("Starting Napari...")
    viewer = napari.Viewer(title=f"Spherical Cell {cell_id} overlay on Ch04")
    
    # Add ch04 as image
    viewer.add_image(ch04_subvol, name='Ch04 Raw Image', colormap='magenta', blending='additive')
    
    # Add labels
    viewer.add_labels(single_cell_labels, name=f'Spherical Cell {cell_id}', opacity=0.7)
    
    # Add full labels context, hidden
    viewer.add_labels(labels_subvol, name='All Cells Context', visible=False, opacity=0.3)
    
    napari.run()

if __name__ == '__main__':
    main()
