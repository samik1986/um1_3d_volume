import os
import napari
import numpy as np
import tifffile
import scipy.ndimage as ndi
import numpy as np
import tifffile

def load_subvolume(path, z_slice, y_slice, x_slice, is_tiff=False):
    if not os.path.exists(path):
        print(f"Warning: {path} not found.")
        return None
    
    if is_tiff:
        # Compressed TIFFs cannot be memmapped. Load to RAM and immediately slice.
        vol = tifffile.imread(path)
        sub = vol[z_slice, y_slice, x_slice].copy()
        del vol
        return sub
    else:
        # Load NPY using mmap to avoid memory blowup
        vol = np.load(path, mmap_mode='r')
        return np.array(vol[z_slice, y_slice, x_slice])

def load_points(path, z_slice, y_slice, x_slice):
    if not os.path.exists(path):
        return None
    pts = np.load(path)
    if len(pts) == 0:
        return pts
    
    # Filter points to only those within the bounding box
    z1, z2 = z_slice.start, z_slice.stop
    y1, y2 = y_slice.start, y_slice.stop
    x1, x2 = x_slice.start, x_slice.stop
    
    mask = (pts[:,0] >= z1) & (pts[:,0] < z2) & \
           (pts[:,1] >= y1) & (pts[:,1] < y2) & \
           (pts[:,2] >= x1) & (pts[:,2] < x2)
           
    pts = pts[mask].copy()
    
    # Adjust coordinates relative to the subvolume
    if len(pts) > 0:
        pts[:,0] -= z1
        pts[:,1] -= y1
        pts[:,2] -= x1
    
    return pts

import argparse

def main():
    parser = argparse.ArgumentParser(description="Visualize a subvolume of the Neurite Detection pipeline outputs.")
    parser.add_argument("--z_start", type=int, default=0, help="Start index for Z axis")
    parser.add_argument("--z_end", type=int, default=181, help="End index for Z axis")
    parser.add_argument("--y_start", type=int, default=1000, help="Start index for Y axis")
    parser.add_argument("--y_end", type=int, default=1500, help="End index for Y axis")
    parser.add_argument("--x_start", type=int, default=2000, help="Start index for X axis")
    parser.add_argument("--x_end", type=int, default=2500, help="End index for X axis")
    args = parser.parse_args()
    
    input_dir = r"c:\Users\banerjee\Desktop\um1_3d_volume"
    output_dir = r"c:\Users\banerjee\Desktop\um1_3d_volume\neurite_detection\pipeline_output"
    
    raw_488_path = os.path.join(input_dir, "B3Well7_1_AN_20260529_233255_Area1_round0_20260529_233740_488_F0044_cmle.tif")
    
    prefix = "B3Well7_1_AN_20260529_233255_Area1_round0_20260529_233740_488_F0044_cmle_"
    
    # Define subvolume slices based on arguments
    z_slice = slice(args.z_start, args.z_end)
    y_slice = slice(args.y_start, args.y_end)
    x_slice = slice(args.x_start, args.x_end)
    
    print(f"Extracting subvolume: Z={z_slice}, Y={y_slice}, X={x_slice}")
    
    # Load 3D Volumes
    raw_488 = load_subvolume(raw_488_path, z_slice, y_slice, x_slice, is_tiff=True)
    
    filt_soma = load_subvolume(os.path.join(output_dir, f"{prefix}filtered_soma_mask.npy"), z_slice, y_slice, x_slice)
    filt_neurite = load_subvolume(os.path.join(output_dir, f"{prefix}filtered_neurite_mask.npy"), z_slice, y_slice, x_slice)
    filt_skel = load_subvolume(os.path.join(output_dir, f"{prefix}filtered_skeleton_mask.npy"), z_slice, y_slice, x_slice)
    
    disc_soma = load_subvolume(os.path.join(output_dir, f"{prefix}discarded_soma_mask.npy"), z_slice, y_slice, x_slice)
    disc_neurite = load_subvolume(os.path.join(output_dir, f"{prefix}discarded_neurite_mask.npy"), z_slice, y_slice, x_slice)
    disc_skel = load_subvolume(os.path.join(output_dir, f"{prefix}discarded_skeleton_mask.npy"), z_slice, y_slice, x_slice)
    
    # Load Points
    filt_555 = load_points(os.path.join(output_dir, f"{prefix}filtered_barcodes_555.npy"), z_slice, y_slice, x_slice)
    filt_640 = load_points(os.path.join(output_dir, f"{prefix}filtered_barcodes_640.npy"), z_slice, y_slice, x_slice)
    
    disc_555 = load_points(os.path.join(output_dir, f"{prefix}discarded_barcodes_555.npy"), z_slice, y_slice, x_slice)
    disc_640 = load_points(os.path.join(output_dir, f"{prefix}discarded_barcodes_640.npy"), z_slice, y_slice, x_slice)

    combined_soma = np.zeros(filt_skel.shape, dtype=bool) if filt_skel is not None else None
    if combined_soma is not None:
        if filt_soma is not None:
            combined_soma |= (filt_soma > 0)
        if disc_soma is not None:
            combined_soma |= (disc_soma > 0)

    print("Launching Napari...")
    viewer = napari.Viewer(ndisplay=3)
    
    scale = (0.5, 0.1102, 0.1102)
    
    if raw_488 is not None:
        viewer.add_image(raw_488, name="Raw 488", colormap="green", blending="additive", scale=scale)
        
    if filt_skel is not None:
        print("Thickening retained skeletons by 2 pixels for better visibility...")
        filt_skel = ndi.binary_dilation(filt_skel, iterations=2)
        if filt_soma is not None or disc_soma is not None:
            dil_filt = ndi.binary_dilation(filt_soma > 0, iterations=2) if filt_soma is not None else np.zeros(filt_skel.shape, dtype=bool)
            dil_disc = ndi.binary_dilation(disc_soma > 0, iterations=10) if disc_soma is not None else np.zeros(filt_skel.shape, dtype=bool)
            dilated_soma = dil_filt | dil_disc
            filt_skel = filt_skel & ~dilated_soma
        viewer.add_image(filt_skel, name="Retained Skeletons", colormap="cyan", blending="additive", scale=scale, opacity=0.8)
        
    if disc_skel is not None:
        print("Thickening discarded skeletons by 2 pixels for better visibility...")
        disc_skel = ndi.binary_dilation(disc_skel, iterations=2)
        if filt_soma is not None or disc_soma is not None:
            dil_filt = ndi.binary_dilation(filt_soma > 0, iterations=2) if filt_soma is not None else np.zeros(disc_skel.shape, dtype=bool)
            dil_disc = ndi.binary_dilation(disc_soma > 0, iterations=10) if disc_soma is not None else np.zeros(disc_skel.shape, dtype=bool)
            dilated_soma = dil_filt | dil_disc
            disc_skel = disc_skel & ~dilated_soma
        viewer.add_image(disc_skel, name="Discarded Skeletons", colormap="red", blending="additive", scale=scale, opacity=0.8)

    if filt_neurite is not None:
        viewer.add_image(filt_neurite, name="Filtered Neurite", colormap="magenta", blending="additive", scale=scale, opacity=0.5)

    if disc_neurite is not None:
        viewer.add_image(disc_neurite, name="Discarded Neurite", colormap="gray", blending="additive", scale=scale, opacity=0.3)
        
    if filt_soma is not None:
        viewer.add_labels(filt_soma, name="Filtered Soma", scale=scale)
        
    if disc_soma is not None:
        viewer.add_labels(disc_soma, name="Discarded Soma", scale=scale, opacity=0.3)
        
    if filt_555 is not None and len(filt_555) > 0:
        viewer.add_points(filt_555, name="Filtered 555", face_color="yellow", size=10, blending="translucent", scale=scale)
    if filt_640 is not None and len(filt_640) > 0:
        viewer.add_points(filt_640, name="Filtered 640", face_color="red", size=10, blending="translucent", scale=scale)
        
    if disc_555 is not None and len(disc_555) > 0:
        viewer.add_points(disc_555, name="Discarded 555", face_color="orange", size=10, blending="translucent", scale=scale)
    if disc_640 is not None and len(disc_640) > 0:
        viewer.add_points(disc_640, name="Discarded 640", face_color="pink", size=10, blending="translucent", scale=scale)
        
    napari.run()

if __name__ == "__main__":
    main()
