import os
import numpy as np
import tifffile
import napari

def main():
    labels_path = r'c:\Users\banerjee\Desktop\um1_3d_volume\neuron_processing\output\dapi_cell_labels.tif'
    ch04_path = r'C:\Users\banerjee\Desktop\um1_3d_volume\docker_cell_detection\F0200_multichannel_cmle_ch04.tif'
    output_dir = r'c:\Users\banerjee\Desktop\um1_3d_volume\neuron_processing\output\custom_crops'
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("Loading volumes (this might take a few seconds)...")
    # Load labels efficiently using memmap
    labels_vol = tifffile.memmap(labels_path)
    
    # Load ch04 fully into memory (3.7 GB)
    ch04_vol = tifffile.imread(ch04_path)
    
    # Start Napari
    viewer = napari.Viewer(title="Interactive Subvolume Cropper")
    
    # Add the layers
    viewer.add_image(ch04_vol, name='Ch04 Raw', colormap='magenta', blending='additive')
    viewer.add_labels(labels_vol, name='DAPI Labels', opacity=0.3, visible=False)
    
    # Add a shapes layer to let the user draw crop boundaries
    shapes_layer = viewer.add_shapes(
        name='Crop Box', 
        shape_type='rectangle', 
        edge_width=5, 
        edge_color='green', 
        face_color='transparent'
    )
    
    print("\n" + "="*60)
    print("INSTRUCTIONS FOR CROPPING:")
    print("1. Select the 'Crop Box' layer on the left side menu.")
    print("2. Click the 'Add rectangle' icon (or press 'R').")
    print("3. Draw a rectangle over the region you want to extract.")
    print("4. Press 'Shift-C' to crop and save the region!")
    print("   (It will extract 60 Z-slices centered on your current view)")
    print("="*60 + "\n")
    
    @viewer.bind_key('Shift-C')
    def crop_and_save(viewer):
        if len(shapes_layer.data) == 0:
            print("Please draw a rectangle in the 'Crop Box' layer first!")
            return
            
        # Get the coordinates of the most recently drawn shape
        shape_data = shapes_layer.data[-1]
        
        # Calculate bounding box
        min_coords = np.min(shape_data, axis=0).astype(int)
        max_coords = np.max(shape_data, axis=0).astype(int)
        
        if len(min_coords) == 3:
            z_slice, y_min, x_min = min_coords
            _, y_max, x_max = max_coords
            
            # Extract +/- 30 slices around the slice where the rectangle was drawn
            z_span = 30
            z_min = max(0, z_slice - z_span)
            z_max = min(ch04_vol.shape[0], z_slice + z_span)
        else:
            # Fallback for 2D data
            y_min, x_min = min_coords
            y_max, x_max = max_coords
            z_slice = viewer.dims.current_step[0]
            z_span = 30
            z_min = max(0, z_slice - z_span)
            z_max = min(ch04_vol.shape[0], z_slice + z_span)
            
        # Clip to volume boundaries
        y_min, y_max = max(0, y_min), min(ch04_vol.shape[1], y_max)
        x_min, x_max = max(0, x_min), min(ch04_vol.shape[2], x_max)
        
        print(f"\nExtracting volume Z:{z_min}-{z_max}, Y:{y_min}-{y_max}, X:{x_min}-{x_max}...")
        
        sub_ch04 = ch04_vol[z_min:z_max, y_min:y_max, x_min:x_max]
        sub_labels = labels_vol[z_min:z_max, y_min:y_max, x_min:x_max]
        
        # Create unique filenames
        crop_idx = (len([f for f in os.listdir(output_dir) if f.endswith('ch04.tif')]) + 1)
        ch04_out = os.path.join(output_dir, f"crop_{crop_idx:03d}_ch04.tif")
        labels_out = os.path.join(output_dir, f"crop_{crop_idx:03d}_labels.tif")
        
        print(f"Saving to {ch04_out}...")
        tifffile.imwrite(ch04_out, sub_ch04)
        
        print(f"Saving to {labels_out}...")
        tifffile.imwrite(labels_out, sub_labels)
        
        print(f"Crop {crop_idx:03d} saved successfully! You can draw another rectangle and press Shift-C again.")
        
    napari.run()

if __name__ == '__main__':
    main()
