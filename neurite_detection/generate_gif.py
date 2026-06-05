import os
import json
import tifffile
import napari
import numpy as np
import imageio

def generate_neurite_gif():
    raw_vol_path = "tutorial_data/synthetic_raw.tif"
    somas_path = "tutorial_data/synthetic_somas.tif"
    cw_json_path = "tutorial_data/synthetic_cw.json"
    
    raw_vol = tifffile.imread(raw_vol_path, out='memmap')
    with open(cw_json_path, 'r') as f:
        cw_data = json.load(f)
        
    viewer = napari.Viewer(show=False)
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
        viewer.add_shapes(line_paths, shape_type='path', edge_color='cyan', edge_width=2, name='1-Cells', scale=(0.5, 0.1, 0.1))
        
    frames = []
    
    viewer.camera.angles = (0, 0, 90)
    viewer.camera.zoom = 1.5
    viewer.text_overlay.visible = True
    viewer.text_overlay.text = "Neurite Proofreading"
    viewer.text_overlay.color = 'yellow'
    frames.append(viewer.screenshot(canvas_only=False))
    
    for i in range(10):
        viewer.camera.angles = (0, i*5, 90)
        frames.append(viewer.screenshot(canvas_only=False))
        
    viewer.text_overlay.text = "Draw Edge & Snap (Press S)"
    if line_paths and len(node_coords) > 2:
        new_path = np.array([node_coords[0], node_coords[2]])
        viewer.layers['1-Cells'].add(new_path, shape_type='path')
    frames.append(viewer.screenshot(canvas_only=False))
    
    for _ in range(3):
        frames.append(viewer.screenshot(canvas_only=False))
        
    imageio.mimsave("proofreading_neurites_demo.gif", frames, fps=5)
    print("Saved proofreading_neurites_demo.gif")
    viewer.close()


def generate_centroid_gif():
    raw_vol_path = "tutorial_data/synthetic_raw.tif"
    swc_path = "tutorial_data/synthetic_centroids.swc"
    
    raw_vol = tifffile.imread(raw_vol_path, out='memmap')
    
    viewer = napari.Viewer(show=False)
    viewer.add_image(raw_vol, name='Raw Volume', scale=(0.5, 0.1, 0.1), colormap='magenta', blending='additive')
    
    coords = []
    with open(swc_path, 'r') as f:
        for line in f:
            if line.startswith('#'): continue
            parts = line.strip().split()
            if len(parts) >= 5:
                coords.append([float(parts[4]), float(parts[3]), float(parts[2])])
    
    viewer.add_points(np.array(coords), name='Centroids', size=8, face_color='cyan', scale=(0.5, 0.1, 0.1))
    
    frames = []
    viewer.camera.angles = (0, 0, 90)
    viewer.camera.zoom = 1.5
    viewer.text_overlay.visible = True
    viewer.text_overlay.text = "Centroid Proofreading"
    viewer.text_overlay.color = 'yellow'
    
    frames.append(viewer.screenshot(canvas_only=False))
    
    for i in range(10):
        viewer.camera.angles = (0, i*5, 90)
        frames.append(viewer.screenshot(canvas_only=False))
        
    viewer.text_overlay.text = "Add missing & Delete False Positives"
    viewer.layers['Centroids'].data = np.array([coords[0], [16, 192, 192]]) # Fix it visually
    frames.append(viewer.screenshot(canvas_only=False))
    
    for _ in range(3):
        frames.append(viewer.screenshot(canvas_only=False))
        
    imageio.mimsave("proofreading_centroids_demo.gif", frames, fps=5)
    print("Saved proofreading_centroids_demo.gif")
    viewer.close()

if __name__ == '__main__':
    generate_neurite_gif()
    generate_centroid_gif()
