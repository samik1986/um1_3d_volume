"""
visualization.py (neuron_detection)

Author: Samik Banerjee
Date: May 8, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

Visualization utilities for Napari, providing automated layer configuration 
for raw volumes, vesselness maps, and skeleton masks.
"""

import napari

def launch_napari(raw_volume, vesselness_map, skeleton, title="3D Neuron Detection"):
    """Launches the Napari viewer with the detection layers."""
    viewer = napari.Viewer(title=title)
    
    viewer.add_image(
        raw_volume, 
        name='Raw Volume', 
        colormap='gray', 
        blending='translucent'
    )
    
    viewer.add_image(
        vesselness_map, 
        name='Vesselness Map', 
        colormap='hot', 
        blending='additive',
        visible=False
    )
    
    viewer.add_labels(
        skeleton.astype(int), 
        name='Detected Neurons (Skeleton)'
    )
    
    print("Visualization ready. Napari is open. Close the window to exit the script.")
    napari.run()
