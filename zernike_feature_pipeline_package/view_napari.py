import napari
import tifffile
import numpy as np

def main():
    orig_path = r'c:\Users\banerjee\Desktop\um1_3d_volume\neuron_processing\output\custom_crops\crop_001_ch04.tif'
    recon_path = r'c:\Users\banerjee\Desktop\um1_3d_volume\neuron_processing\output\custom_crops\crop_001_ch04_reconstructed.tif'
    
    orig_vol = tifffile.imread(orig_path)
    recon_vol = tifffile.imread(recon_path)
    
    # Optional: Match their scales visually
    # We can normalize them to 0-1 for visualization if desired, 
    # but napari's contrast limits handle this automatically well enough.
    
    viewer = napari.Viewer()
    
    # The true physical voxel spacing is (0.5, 0.1102, 0.1102)
    voxel_scale = (0.5, 0.1102, 0.1102)
    
    # Add original volume
    viewer.add_image(orig_vol, name='Original Volume', colormap='green', blending='additive', scale=voxel_scale)
    
    # Add reconstructed volume
    viewer.add_image(recon_vol, name='Reconstructed N=6', colormap='magenta', blending='additive', scale=voxel_scale)
    
    # Set to 3D view
    viewer.dims.ndisplay = 3
    
    napari.run()

if __name__ == '__main__':
    main()
