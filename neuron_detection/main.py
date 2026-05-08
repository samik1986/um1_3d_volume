"""
main.py (neuron_detection)

Author: Samik Banerjee
Date: May 8, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

Main orchestrator for the modular neuron detection pipeline. 
Processes large volumes in chunks, extracts topological graphs, and stitches them.
"""

import os
from io_utils import load_tiff_memmap, extract_subvolume
from processing import preprocess_volume, apply_frangi_3d, extract_skeleton
from visualization import launch_napari

def main():
    # 1. Determine input file path
    input_file = '../docker_cell_detection/F0200_multichannel_cmle_ch03.tif'
    if not os.path.exists(input_file):
        input_file = 'docker_cell_detection/F0200_multichannel_cmle_ch03.tif'
    if not os.path.exists(input_file):
        input_file = 'F0200_multichannel_cmle_ch03.tif'
        
    print(f"[1] Opening volume: {input_file}")
    try:
        vol_mmap = load_tiff_memmap(input_file)
        print(f"    Volume mapped. Full shape: {vol_mmap.shape}")
    except Exception as e:
        print(f"    Error mapping volume: {e}")
        return
    # 2. Define chunk size
    z, y, x = vol_mmap.shape
    
    # Using larger chunks to reduce total number of iterations
    # 680x680x136 = 32 chunks total for the 4GB volume
    chunk_z, chunk_y, chunk_x = 136, 680, 680
    
    print(f"\n[2] Processing full volume in chunks of {chunk_z}x{chunk_y}x{chunk_x}...")
    
    graphs = []
    
    for z_start in range(0, z, chunk_z):
        for y_start in range(0, y, chunk_y):
            for x_start in range(0, x, chunk_x):
                z_end = min(z_start + chunk_z, z)
                y_end = min(y_start + chunk_y, y)
                x_end = min(x_start + chunk_x, x)
                
                print(f"  -> Processing Chunk Z[{z_start}:{z_end}], Y[{y_start}:{y_end}], X[{x_start}:{x_end}]")
                subvol = extract_subvolume(vol_mmap, (z_start, z_end), (y_start, y_end), (x_start, x_end))
                
                from processing import process_subvolume_to_graph
                # Extract graph with global offset
                graph = process_subvolume_to_graph(subvol, global_offset=(z_start, y_start, x_start))
                
                if graph.number_of_nodes() > 0:
                    graphs.append(graph)
                
    # 3. Stitch graphs
    from graph_utils import stitch_graphs, graph_to_cw_complex, graph_to_swc
    
    print("\n[3] Stitching subvolume graphs...")
    final_graph = stitch_graphs(graphs, merge_dist=3.0)
    
    # 4. Save Vector Data
    print("\n[4] Saving vector outputs...")
    graph_to_cw_complex(final_graph, "full_volume_stitched.json")
    graph_to_swc(final_graph, "full_volume_stitched.swc")
    
    # 5. Launch Napari with Vector Overlay
    print("\n[5] Launching Napari Visualization...")
    # To overlay the graph, we extract the path coordinates
    paths = []
    for u, v, key, data in final_graph.edges(keys=True, data=True):
        pts = data.get('pts', [])
        if len(pts) > 0:
            paths.append(pts)
            
    import napari
    viewer = napari.Viewer(title="Full Volume Vector Neurons")
    viewer.add_image(vol_mmap, name='Raw Volume', colormap='gray', blending='translucent')
    
    if paths:
        viewer.add_shapes(paths, shape_type='path', edge_color='red', edge_width=2, name='Stitched Neurons', ndim=3)
        
    napari.run()

if __name__ == "__main__":
    main()
