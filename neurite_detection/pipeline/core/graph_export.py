import os
import json
import numpy as np
import sknw
from scipy import ndimage

def export_graphs(binary_skel, output_dir, scale_z, scale_y, scale_x, centroids_488=None, out_prefix=""):
    print(f"\n--- Tracing Skeletons to Graph (Component by Component) ---")
    os.makedirs(output_dir, exist_ok=True)
    
    cw_complex_path = os.path.join(output_dir, f"{out_prefix}cw_complex.json")
    swc_path = os.path.join(output_dir, f"{out_prefix}skeletons.swc")
    cw_complex_scaled_path = os.path.join(output_dir, f"{out_prefix}cw_complex_micrometers.json")
    swc_scaled_path = os.path.join(output_dir, f"{out_prefix}skeletons_micrometers.swc")
    
    f_swc = open(swc_path, 'w')
    f_swc_scaled = open(swc_scaled_path, 'w')
    f_json = open(cw_complex_path, 'w')
    f_json_scaled = open(cw_complex_scaled_path, 'w')
    
    f_swc.write("# Skeletons converted from sknw\n# Units: voxels\n# Node Types: 3=Skeleton, 2=Cell_488\n")
    f_swc_scaled.write(f"# Skeletons converted from sknw (Scaled Z={scale_z}, Y={scale_y}, X={scale_x})\n# Units: micrometers\n# Node Types: 3=Skeleton, 2=Cell_488\n")
    
    f_json.write('{\n  "metadata": {"units": "voxels"},\n  "cells_0_nodes": [\n')
    f_json_scaled.write('{\n  "metadata": {"units": "micrometers", "scale_factors": {"Z": ' + str(scale_z) + ', "Y": ' + str(scale_y) + ', "X": ' + str(scale_x) + '}},\n  "cells_0_nodes": [\n')
    
    global_node_id = 1
    
    # Process cells
    first_node = True
    if centroids_488 is not None:
        for c in centroids_488:
            z, y, x = float(c[0]), float(c[1]), float(c[2])
            z_sc, y_sc, x_sc = z * scale_z, y * scale_y, x * scale_x
            curr_id = global_node_id
            global_node_id += 1
            
            if not first_node:
                f_json.write(',\n')
                f_json_scaled.write(',\n')
            first_node = False
            
            f_json.write(json.dumps({"node_id": curr_id, "coord": [z, y, x], "type": "cell_488"}))
            f_json_scaled.write(json.dumps({"node_id": curr_id, "coord": [z_sc, y_sc, x_sc], "type": "cell_488"}))
            f_swc.write(f"{curr_id} 2 {x:.3f} {y:.3f} {z:.3f} 5.0 -1\n")
            f_swc_scaled.write(f"{curr_id} 2 {x_sc:.5f} {y_sc:.5f} {z_sc:.5f} 5.0 -1\n")

    # Get connected components
    print("Labeling connected skeleton components...")
    # Use ndimage.label on the 3D boolean skeleton
    labeled_skel, num_features = ndimage.label(binary_skel)
    print(f"Found {num_features} independent skeleton components.")
    
    # We can delete binary_skel to free up 1.3GB since we have labeled_skel
    del binary_skel
    import gc
    gc.collect()
    
    print("Finding bounding boxes for components...")
    objects = ndimage.find_objects(labeled_skel)
    
    # We will need to store linestrings temporarily because JSON requires all nodes first, then linestrings.
    # We can stream linestrings to a temporary file.
    import tempfile
    temp_lines_file = tempfile.TemporaryFile(mode='w+')
    temp_lines_scaled_file = tempfile.TemporaryFile(mode='w+')
    
    first_line = True
    
    print("Tracing components one by one...")
    for i, slice_tuple in enumerate(objects):
        if slice_tuple is None:
            continue
            
        label_id = i + 1
        
        # Extract small cropped region and pad by 1 to prevent sknw boundary errors
        crop_labeled = labeled_skel[slice_tuple]
        crop_binary = (crop_labeled == label_id)
        crop_binary = np.pad(crop_binary, pad_width=1, mode='constant', constant_values=False)
        
        # Build sknw graph for just this component
        graph = sknw.build_sknw(crop_binary, multi=True)
        
        z_offset = slice_tuple[0].start - 1
        y_offset = slice_tuple[1].start - 1
        x_offset = slice_tuple[2].start - 1
        
        # Nodes streaming
        for (s, e, k) in graph.edges(keys=True):
            pts = graph[s][e][k]['pts']
            parent_swc_id = -1
            
            for pt_idx in range(len(pts)):
                curr = pts[pt_idx]
                z = float(curr[0]) + z_offset
                y = float(curr[1]) + y_offset
                x = float(curr[2]) + x_offset
                
                z_sc, y_sc, x_sc = z * scale_z, y * scale_y, x * scale_x
                
                curr_swc_id = global_node_id
                global_node_id += 1
                
                if not first_node:
                    f_json.write(',\n')
                    f_json_scaled.write(',\n')
                first_node = False
                
                f_json.write(json.dumps({"node_id": curr_swc_id, "coord": [z, y, x], "type": "skeleton"}))
                f_json_scaled.write(json.dumps({"node_id": curr_swc_id, "coord": [z_sc, y_sc, x_sc], "type": "skeleton"}))
                
                f_swc.write(f"{curr_swc_id} 3 {x:.3f} {y:.3f} {z:.3f} 1.0 {parent_swc_id}\n")
                f_swc_scaled.write(f"{curr_swc_id} 3 {x_sc:.5f} {y_sc:.5f} {z_sc:.5f} 1.0 {parent_swc_id}\n")
                
                parent_swc_id = curr_swc_id
                
        # Linestrings streaming to temp file
        for (s, e, k) in graph.edges(keys=True):
            pts = graph[s][e][k]['pts']
            
            for pt_idx in range(1, len(pts)):
                pz = float(pts[pt_idx-1][0]) + z_offset
                py = float(pts[pt_idx-1][1]) + y_offset
                px = float(pts[pt_idx-1][2]) + x_offset
                
                z = float(pts[pt_idx][0]) + z_offset
                y = float(pts[pt_idx][1]) + y_offset
                x = float(pts[pt_idx][2]) + x_offset
                
                pz_sc, py_sc, px_sc = pz * scale_z, py * scale_y, px * scale_x
                z_sc, y_sc, x_sc = z * scale_z, y * scale_y, x * scale_x
                
                if not first_line:
                    temp_lines_file.write(',\n')
                    temp_lines_scaled_file.write(',\n')
                first_line = False
                
                temp_lines_file.write(json.dumps({"geometry": [[pz, py, px], [z, y, x]]}))
                temp_lines_scaled_file.write(json.dumps({"geometry": [[pz_sc, py_sc, px_sc], [z_sc, y_sc, x_sc]]}))
        
        if (i+1) % 5000 == 0:
            print(f"  Processed {i+1}/{num_features} components...")
            
    del labeled_skel
    gc.collect()

    f_json.write('\n  ],\n  "cells_1_linestrings": [\n')
    f_json_scaled.write('\n  ],\n  "cells_1_linestrings": [\n')
    
    # Read temp files and append
    temp_lines_file.seek(0)
    for chunk in iter(lambda: temp_lines_file.read(1024*1024), ''):
        f_json.write(chunk)
        
    temp_lines_scaled_file.seek(0)
    for chunk in iter(lambda: temp_lines_scaled_file.read(1024*1024), ''):
        f_json_scaled.write(chunk)
        
    temp_lines_file.close()
    temp_lines_scaled_file.close()
            
    f_json.write('\n  ]\n}\n')
    f_json_scaled.write('\n  ]\n}\n')
    
    f_swc.close()
    f_swc_scaled.close()
    f_json.close()
    f_json_scaled.close()
    
    print(f"Exported scaled & unscaled Graphs to: {output_dir}")
