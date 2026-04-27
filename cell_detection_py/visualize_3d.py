import tifffile
import numpy as np
import plotly.graph_objects as go
import pandas as pd
import os

def load_swc(filename):
    """Loads centroids from an SWC file."""
    try:
        # SWC format: id type x y z radius parent
        # Skip comments
        data = pd.read_csv(filename, sep=' ', comment='#', header=None, 
                          names=['id', 'type', 'x', 'y', 'z', 'r', 'p'])
        return data
    except Exception as e:
        print(f"Error loading SWC: {e}")
        return None

def visualize():
    input_file = 'F0200_multichannel_cmle_ch04.tif'
    swc_file = 'centroids.swc'
    
    if not os.path.exists(input_file):
        input_file = os.path.join('..', input_file)
    if not os.path.exists(swc_file):
        swc_file = os.path.join('..', swc_file)
    
    if not os.path.exists(input_file):
        print(f"File {input_file} not found.")
        return

    print("Loading SWC data...")
    centroids_df = load_swc(swc_file)
    
    print("Loading and downsampling volume for visualization...")
    # We load every 16th pixel in XY to keep memory low for Plotly
    ds_factor = 16
    with tifffile.TiffFile(input_file) as tif:
        pages = tif.pages
        num_slices = len(pages)
        h, w = pages[0].shape
        
        # Initialize downsampled volume
        # Z remains the same resolution, XY downsampled
        V_ds = np.zeros((h // ds_factor, w // ds_factor, num_slices), dtype=np.uint16)
        
        for z in range(num_slices):
            img = pages[z].asarray()
            V_ds[:, :, z] = img[::ds_factor, ::ds_factor]
    
    print("Preparing 3D Visualization...")
    
    # Coordinates for the volume
    x = np.linspace(0, w, V_ds.shape[1])
    y = np.linspace(0, h, V_ds.shape[0])
    z = np.arange(num_slices)
    
    # Create the volume plot
    # We use a lower opacity and specific color scale
    X_grid, Y_grid, Z_grid = np.meshgrid(x, y, z)
    
    fig = go.Figure()

    # Add Centroids as Scatter3D
    if centroids_df is not None:
        fig.add_trace(go.Scatter3d(
            x=centroids_df['x'],
            y=centroids_df['y'],
            z=centroids_df['z'],
            mode='markers',
            marker=dict(
                size=3,
                color='red',
                opacity=0.8
            ),
            name='Centroids'
        ))

    # Add Volume rendering
    # Flatten the grids for Plotly Volume
    fig.add_trace(go.Volume(
        x=X_grid.flatten(),
        y=Y_grid.flatten(),
        z=Z_grid.flatten(),
        value=V_ds.flatten(),
        isomin=np.percentile(V_ds, 95), # Only show high intensity (cells/vessels)
        isomax=V_ds.max(),
        opacity=0.1, # Keep it transparent to see through
        surface_count=15,
        colorscale='Viridis',
        name='Volume'
    ))

    fig.update_layout(
        title='3D Cell Centroid Detection Overlay',
        scene=dict(
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z (Slice)',
            aspectmode='data' # Keep spatial proportions
        ),
        margin=dict(l=0, r=0, b=0, t=40)
    )

    print("Saving visualization to cell_viz_3d.html...")
    fig.write_html("cell_viz_3d.html")
    print("Done. Open cell_viz_3d.html in your browser to view.")

if __name__ == '__main__':
    visualize()
