import os
import json
import tifffile
import napari
import numpy as np
import imageio

def run():
    raw_vol_path = "tutorial_data/tutorial_crop.tif"
    somas_path = "output/tutorial_crop/soma_labels.tif"
    mask_vol_path = "output/tutorial_crop/neurite_mask.tif"
    cw_json_path = "output/tutorial_crop/cw_complex.json"
    
    raw_vol = tifffile.imread(raw_vol_path, out='memmap')
    with open(cw_json_path, 'r') as f:
        cw_data = json.load(f)
        
    viewer = napari.Viewer(show=False)
    
    # Setup layers (simplified for speed)
    viewer.add_image(raw_vol, name='Raw Volume', scale=(0.5, 0.1, 0.1), colormap='magenta', blending='additive')
    soma_labels = tifffile.imread(somas_path, out='memmap')
    viewer.add_labels(soma_labels, name='Detected Somas', scale=(0.5, 0.1, 0.1), opacity=0.8)
    
    nodes = cw_data.get('cells_0_nodes', [])
    node_coords = [n['coord'] for n in nodes]
    if node_coords:
        viewer.add_points(np.array(node_coords), name='0-Cells (Nodes)', size=3, face_color='red', scale=(0.5, 0.1, 0.1))
        
    lines = cw_data.get('cells_1_linestrings', [])
    line_paths = [l['geometry'] for l in lines]
    if line_paths:
        viewer.add_shapes(line_paths, shape_type='path', edge_color='green', edge_width=2, name='1-Cells', scale=(0.5, 0.1, 0.1))
        
    # Generate frames
    frames = []
    
    # 1. Show raw data
    viewer.camera.angles = (0, 0, 90)
    viewer.camera.zoom = 1.5
    viewer.text_overlay.visible = True
    viewer.text_overlay.text = "Step 1: Inspect Raw Data & Somas"
    viewer.text_overlay.color = 'yellow'
    frames.append(viewer.screenshot(canvas_only=False))
    
    # 2. Add some rotation
    for i in range(10):
        viewer.camera.angles = (0, i*5, 90)
        frames.append(viewer.screenshot(canvas_only=False))
        
    # 3. Simulate adding an edge
    viewer.text_overlay.text = "Step 2: Draw a new edge between nodes"
    if line_paths and len(node_coords) > 2:
        new_path = np.array([node_coords[0], node_coords[1]])
        viewer.layers['1-Cells'].add(new_path, shape_type='path')
    frames.append(viewer.screenshot(canvas_only=False))
    
    # 4. Save
    viewer.text_overlay.text = "Step 3: Press 'S' to mathematically snap the edge!"
    for _ in range(3):
        frames.append(viewer.screenshot(canvas_only=False))
        
    imageio.mimsave("proofreading_demo.gif", frames, fps=5)
    print("Saved proofreading_demo.gif")
    viewer.close()

if __name__ == '__main__':
    run()
