"""
swc_proofreader.py (neurite_detection/pipeline/visualization)

Interactive Napari proofreader for annotating or correcting SWC skeleton topologies 
with auto-snapping to intensity via CuPy and tiled Dask loading.
"""

import os
import napari
import tifffile
import numpy as np
import dask.array as da
import zarr
from qtpy.QtWidgets import QMessageBox
from scipy.spatial import KDTree

try:
    import cupy as cp
    use_gpu = cp.is_available()
except ImportError:
    use_gpu = False

def run_swc_proofreader(raw_488_path, swc_path=None, out_swc_path=None):
    if out_swc_path is None:
        if swc_path:
            base, ext = os.path.splitext(swc_path)
            out_swc_path = f"{base}_proofread{ext}"
        else:
            base = os.path.splitext(raw_488_path)[0]
            out_swc_path = f"{base}_proofread.swc"
            
    print(f"\n--- Launching Napari SWC Proofreader (De Novo) ---")
    # Launch in 2D mode by default. 3D mode forces Dask to evaluate the entire 3.7GB array into RAM, causing OOM.
    # The user can toggle 3D mode in the Napari GUI if they have sufficient RAM.
    viewer = napari.Viewer(ndisplay=2)
    
    print("Loading 488 Raw Volume (Lazy Multi-Page Dask)...")
    try:
        from dask import delayed
        # Use delayed loading to avoid reading the whole file at once
        @delayed
        def load_page(path, index):
            with tifffile.TiffFile(path) as t:
                return t.pages[index].asarray()

        with tifffile.TiffFile(raw_488_path) as tif:
            num_pages = len(tif.pages)
            if num_pages > 1:
                sample = tif.pages[0].asarray()
                lazy_arrays = [
                    da.from_delayed(load_page(raw_488_path, i), shape=sample.shape, dtype=sample.dtype) 
                    for i in range(num_pages)
                ]
                img_488 = da.stack(lazy_arrays, axis=0)
                print(f"Loaded lazily as dask array. Shape: {img_488.shape}")
            else:
                img_488 = tif.asarray()
                print("Single page TIF, loaded to RAM.")
    except Exception as e:
        print(f"Failed to load lazily: {e}. Falling back to standard imread...")
        img_488 = tifffile.imread(raw_488_path)
    
    scale_factor = (0.5, 0.1102, 0.1102)
    viewer.add_image(img_488, name="Raw 488", colormap="green", blending="additive", scale=scale_factor)
    
    paths = []
    if swc_path and os.path.exists(swc_path):
        print(f"Loading SWC file: {swc_path}")
        nodes = {}
        with open(swc_path, 'r') as fp:
            for line in fp:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split()
                if len(parts) >= 7:
                    nid = int(parts[0])
                    x, y, z = float(parts[2]), float(parts[3]), float(parts[4])
                    pid = int(parts[6])
                    nodes[nid] = {'coord': [z, y, x], 'parent': pid}
        
        for nid, node in nodes.items():
            pid = node['parent']
            if pid != -1 and pid in nodes:
                paths.append(np.array([nodes[pid]['coord'], node['coord']]))
    
    shapes_layer = viewer.add_shapes(
        paths, 
        shape_type='path', 
        edge_width=1.5, 
        edge_color='cyan', 
        name="SWC Paths", 
        scale=scale_factor,
        ndim=3
    )
    
    window = 5 # +/- 5 voxels
    max_z, max_y, max_x = img_488.shape

    def perform_snap(data):
        if not data:
            return data, False
            
        snapped = False
        new_data = []
        for path in data:
            new_path = []
            for pt in path:
                z, y, x = pt
                zi, yi, xi = int(round(z)), int(round(y)), int(round(x))
                
                z_min = max(0, zi - window)
                z_max = min(max_z, zi + window + 1)
                y_min = max(0, yi - window)
                y_max = min(max_y, yi + window + 1)
                x_min = max(0, xi - window)
                x_max = min(max_x, xi + window + 1)
                
                sub_img_lazy = img_488[z_min:z_max, y_min:y_max, x_min:x_max]
                if sub_img_lazy.size == 0:
                    new_path.append(pt)
                    continue
                
                if isinstance(sub_img_lazy, da.Array):
                    sub_img = sub_img_lazy.compute()
                else:
                    sub_img = sub_img_lazy
                    
                if use_gpu:
                    try:
                        sub_img_gpu = cp.asarray(sub_img)
                        loc_flat = cp.argmax(sub_img_gpu)
                        loc = cp.unravel_index(loc_flat, sub_img_gpu.shape)
                        loc = [int(l.get()) for l in loc]
                    except Exception as e:
                        print("GPU snap failed, falling back to CPU", e)
                        loc = np.unravel_index(np.argmax(sub_img), sub_img.shape)
                else:
                    loc = np.unravel_index(np.argmax(sub_img), sub_img.shape)
                    
                new_z = z_min + loc[0]
                new_y = y_min + loc[1]
                new_x = x_min + loc[2]
                
                if (new_z != z) or (new_y != y) or (new_x != x):
                    snapped = True
                new_path.append([new_z, new_y, new_x])
            new_data.append(np.array(new_path))
        return new_data, snapped

    @shapes_layer.mouse_drag_callbacks.append
    def snap_on_release(layer, event):
        yield  # Wait for drag to start
        while event.type == 'mouse_move':
            yield  # While dragging, do nothing
        # On release, snap the shape data
        print("Mouse released, triggering auto-snap...")
        data = layer.data
        new_data, snapped = perform_snap(data)
        if snapped:
            layer.data = new_data
            print("Vertices snapped to local maxima.")

    # Compile graph and save
    @viewer.bind_key('Shift-S')
    def save_swc(viewer):
        print(f"Compiling graph and saving to {out_swc_path}...")
        data = shapes_layer.data
        if not data:
            print("No paths to save.")
            return
            
        vertices = []
        for path in data:
            for pt in path:
                vertices.append(pt)
                
        if not vertices:
            return
            
        vertices = np.array(vertices)
        
        tree = KDTree(vertices)
        merged_vertices = []
        vertex_map = {} 
        
        for i, v in enumerate(vertices):
            if i in vertex_map:
                continue
            idx = len(merged_vertices)
            merged_vertices.append(v)
            neighbors = tree.query_ball_point(v, 2.0)
            for n in neighbors:
                if n not in vertex_map:
                    vertex_map[n] = idx
                    
        adj = {i: set() for i in range(len(merged_vertices))}
        idx = 0
        for path in data:
            for i in range(len(path) - 1):
                v1 = vertex_map[idx + i]
                v2 = vertex_map[idx + i + 1]
                if v1 != v2:
                    adj[v1].add(v2)
                    adj[v2].add(v1)
            idx += len(path)
            
        visited = set()
        swc_nodes = []
        node_counter = 1
        
        for start_node in range(len(merged_vertices)):
            if start_node in visited:
                continue
                
            queue = [(start_node, -1)]
            visited.add(start_node)
            
            while queue:
                curr, parent_swc = queue.pop(0)
                curr_swc = node_counter
                node_counter += 1
                
                pt = merged_vertices[curr]
                swc_nodes.append((curr_swc, 3, pt[2], pt[1], pt[0], 1.0, parent_swc))
                
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, curr_swc))
                        
        try:
            with open(out_swc_path, 'w') as f:
                f.write("# De Novo Proofread SWC file\\n")
                f.write("# Node Types: 3=Skeleton, 2=Cell_488\\n")
                for node in swc_nodes:
                    nid, ntype, x, y, z, radius, pid = node
                    f.write(f"{nid} {ntype} {x:.3f} {y:.3f} {z:.3f} {radius} {pid}\\n")
            
            print(f"Saved {len(swc_nodes)} nodes to {out_swc_path}")
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("Saved SWC successfully!")
            msg.setInformativeText(f"File saved to:\n{out_swc_path}\nNodes: {len(swc_nodes)}")
            msg.setWindowTitle("Save Success")
            msg.exec_()
            
        except Exception as e:
            print(f"Failed to save SWC: {e}")

    print("\n--- Controls ---")
    print(" - Use the 'Add Path' tool to draw lines in 3D.")
    print(" - Use the 'Select Vertex' tool to move existing points.")
    print(" - Points auto-snap to the highest intensity on MOUSE RELEASE.")
    print(f" - GPU Snapping Backend: {'CuPy' if use_gpu else 'NumPy (CPU)'}")
    print(" - Press 'Shift+S' to merge close paths and save to SWC.")
    print("Viewer Ready. Close window to exit.")
    
    napari.run()
