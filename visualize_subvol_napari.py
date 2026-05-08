"""
visualize_subvol_napari.py

Author: Samik Banerjee
Date: May 8, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

Visualize subvolumes (raw vs reconstructed) in 3D using Napari.
"""

import napari
import nrrd
import os

def visualize_subvol():
    raw_path = r"c:\Users\banerjee\Desktop\um1_3d_volume\fp_pipeline_output\SubVol1_Raw.nrrd"
    recon_path = r"c:\Users\banerjee\Desktop\um1_3d_volume\fp_pipeline_output\SubVol1_Recon.nrrd"
    
    if not os.path.exists(raw_path):
        print(f"Error: Could not find {raw_path}")
        return
    if not os.path.exists(recon_path):
        print(f"Error: Could not find {recon_path}")
        return

    print(f"Loading raw volume from {raw_path}...")
    raw_data, raw_header = nrrd.read(raw_path)
    
    print(f"Loading reconstructed volume from {recon_path}...")
    recon_data, recon_header = nrrd.read(recon_path)
    
    # nrrd loads as (X, Y, Z) usually. We transpose to (Z, Y, X) for Napari
    # so that Z is the first dimension (which Napari treats as depth/scroll axis)
    raw_data = raw_data.transpose(2, 1, 0)
    recon_data = recon_data.transpose(2, 1, 0)
    
    # Downsample the data for responsiveness
    ds = 2
    print(f"Downsampling data by a factor of {ds}...")
    raw_data_ds = raw_data[::ds, ::ds, ::ds]
    recon_data_ds = recon_data[::ds, ::ds, ::ds]
    
    # Set the scale based on resolution: (z_res, y_res, x_res)
    # Since we downsampled by `ds`, we multiply the base resolution by `ds`
    z_res, y_res, x_res = 0.5, 0.1102, 0.1102
    voxel_scale = (z_res * ds, y_res * ds, x_res * ds)
    
    print("Opening Napari Viewer...")
    viewer = napari.Viewer(title="SubVol1 Raw vs Recon Overlay (Downsampled)")
    
    # Add raw volume
    viewer.add_image(
        raw_data_ds,
        name=f"SubVol1_Raw (ds={ds})",
        colormap="gray",
        blending="additive",
        rendering="mip",
        scale=voxel_scale
    )
    
    # Add reconstructed volume overlay
    viewer.add_image(
        recon_data_ds,
        name=f"SubVol1_Recon (ds={ds})",
        colormap="green",
        blending="additive",
        opacity=0.6,
        rendering="mip",
        scale=voxel_scale
    )
    
    print("Visualization ready. You can toggle visibility and adjust opacity in the Napari layers panel.")
    
    # Set to 3D view automatically
    viewer.dims.ndisplay = 3
    
    napari.run()

if __name__ == "__main__":
    visualize_subvol()
