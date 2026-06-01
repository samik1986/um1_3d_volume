"""
napari_proofreader.py

Interactive Napari-based proofreading tool for 3D DAPI volumes and centroids.
Created by: Samik Banerjee @ Mitralab @ CSHL
Includes custom UI buttons for loading datasets, adjusting marker sizes, and saving edited SWC centroids.
"""

import os
import sys
import numpy as np
import pandas as pd
import tifffile
import napari
from magicgui import magicgui
from qtpy.QtCore import QThread, Signal, QObject
from qtpy.QtWidgets import QFileDialog, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QDoubleSpinBox, QProgressBar, QApplication



# Helper to read SWC files
def read_swc(filepath):
    """
    Reads an SWC file and returns a pandas DataFrame.
    Format: id type x y z r p
    """
    if not os.path.exists(filepath):
        print(f"Error: {filepath} does not exist.")
        return None
    try:
        # Standard SWC uses space as separator and '#' for comments
        df = pd.read_csv(filepath, sep=' ', comment='#', header=None,
                         names=['id', 'type', 'x', 'y', 'z', 'r', 'p'])
        return df
    except Exception as e:
        print(f"Error reading SWC: {e}")
        return None

def save_swc(filepath, coords, marker_size=1.0):
    """
    Saves centroids coordinates (in physical units or pixel units, depending on scale) back to SWC.
    Here coords are in physical units (Z, Y, X) because Napari displays/edits them scaled, 
    but let's write them matching the original SWC structure.
    coords: numpy array of shape (N, 3) representing (z, y, x) in physical space.
    """
    try:
        with open(filepath, 'w') as f:
            f.write("# SWC file edited and saved using Napari Proofreader\n")
            f.write("# id type x y z radius parent\n")
            # In SWC, order is x, y, z
            for idx, pt in enumerate(coords):
                z_phys, y_phys, x_phys = pt
                # ID starts at 1, type=1 (soma/centroid), parent=-1
                f.write(f"{idx+1} 1 {x_phys:.6f} {y_phys:.6f} {z_phys:.6f} {marker_size:.6f} -1\n")
        print(f"Successfully saved {len(coords)} centroids to {filepath}")
        return True
    except Exception as e:
        print(f"Error saving SWC: {e}")
        return False
        
# Thread worker for reading files in background
class LoadingWorker(QObject):
    finished = Signal(object, str, str)  # Emits (data, file_type, name)
    progress = Signal(int)
    error = Signal(str)

    def __init__(self, filepath, file_type):
        super().__init__()
        self.filepath = filepath
        self.file_type = file_type

    def run(self):
        try:
            self.progress.emit(10)
            name = os.path.basename(self.filepath)
            if self.file_type == "volume":
                self.progress.emit(30)
                # Load volume chunk/file
                vol = tifffile.imread(self.filepath)
                self.progress.emit(80)
                self.finished.emit(vol, "volume", name)
            elif self.file_type == "centroids":
                self.progress.emit(40)
                df = read_swc(self.filepath)
                self.progress.emit(80)
                self.finished.emit(df, "centroids", name)
            self.progress.emit(100)
        except Exception as e:
            self.error.emit(str(e))


# Custom widgets and layout for napari panel
class ProofreaderDockWidget(QWidget):
    def __init__(self, viewer):
        super().__init__()
        self.viewer = viewer
        self.layout = QVBoxLayout()
        
        # Title Label
        self.title_lbl = QLabel("<b>Proofreading Tools</b><br><font size='2' color='gray'>Samik Banerjee @ Mitralab @ CSHL</font>")
        self.layout.addWidget(self.title_lbl)
        
        # Load Volume Button
        self.btn_load_vol = QPushButton("Upload Volume (.tif)")
        self.btn_load_vol.clicked.connect(self.load_volume_dialog)
        self.layout.addWidget(self.btn_load_vol)
        
        # Load Centroids Button
        self.btn_load_centroids = QPushButton("Upload Centroids (.swc)")
        self.btn_load_centroids.clicked.connect(self.load_centroids_dialog)
        self.layout.addWidget(self.btn_load_centroids)
        
        # Spacing inputs: X, Y, Z
        self.lbl_spacing = QLabel("<b>Voxel Spacing (Z, Y, X):</b>")
        self.layout.addWidget(self.lbl_spacing)
        
        self.layout_spacing = QHBoxLayout()
        
        self.spin_z = QDoubleSpinBox()
        self.spin_z.setRange(0.0001, 100.0)
        self.spin_z.setValue(0.5)
        self.spin_z.setSingleStep(0.1)
        self.spin_z.setPrefix("Z: ")
        self.spin_z.valueChanged.connect(self.update_voxel_spacing)
        
        self.spin_y = QDoubleSpinBox()
        self.spin_y.setRange(0.0001, 100.0)
        self.spin_y.setValue(0.1102)
        self.spin_y.setSingleStep(0.01)
        self.spin_y.setPrefix("Y: ")
        self.spin_y.valueChanged.connect(self.update_voxel_spacing)
        
        self.spin_x = QDoubleSpinBox()
        self.spin_x.setRange(0.0001, 100.0)
        self.spin_x.setValue(0.1102)
        self.spin_x.setSingleStep(0.01)
        self.spin_x.setPrefix("X: ")
        self.spin_x.valueChanged.connect(self.update_voxel_spacing)
        
        self.layout_spacing.addWidget(self.spin_z)
        self.layout_spacing.addWidget(self.spin_y)
        self.layout_spacing.addWidget(self.spin_x)
        self.layout.addLayout(self.layout_spacing)

        # Marker Size SpinBox/Control
        self.lbl_marker_size = QLabel("Marker Size (Physical Units):")
        self.layout.addWidget(self.lbl_marker_size)
        
        self.spin_marker_size = QDoubleSpinBox()
        self.spin_marker_size.setRange(0.01, 100.0)
        self.spin_marker_size.setSingleStep(0.5)
        self.spin_marker_size.setValue(5.0)
        self.spin_marker_size.valueChanged.connect(self.update_marker_size)
        self.layout.addWidget(self.spin_marker_size)
        
        # Save Edits Button
        self.btn_save = QPushButton("Save Edits")
        self.btn_save.clicked.connect(self.save_edits_dialog)
        self.layout.addWidget(self.btn_save)
        
        # Spacer
        self.layout.addWidget(QLabel("<b>Metrics Comparison</b>"))
        
        # Load Baseline SWC Button
        self.btn_load_baseline = QPushButton("Load Baseline SWC (Ground Truth)")
        self.btn_load_baseline.clicked.connect(self.load_baseline_dialog)
        self.layout.addWidget(self.btn_load_baseline)
        
        # Match Tolerance
        self.lbl_tolerance = QLabel("Match Tolerance (Physical Units):")
        self.layout.addWidget(self.lbl_tolerance)
        self.spin_tolerance = QDoubleSpinBox()
        self.spin_tolerance.setRange(0.01, 100.0)
        self.spin_tolerance.setValue(10.0)
        self.spin_tolerance.setSingleStep(1.0)
        self.spin_tolerance.valueChanged.connect(self.calculate_metrics)
        self.layout.addWidget(self.spin_tolerance)
        
        # Stats Output text area
        self.lbl_metrics_stats = QLabel("TP: - | FP: - | FN: -<br>Precision: - | Recall: - | F1: -")
        self.lbl_metrics_stats.setStyleSheet("border: 1px solid gray; padding: 5px; background-color: #2b2b2b; color: #a9b7c6;")
        self.layout.addWidget(self.lbl_metrics_stats)
        
        # Loading Progress Bar
        self.lbl_progress = QLabel("Status: Ready")
        self.layout.addWidget(self.lbl_progress)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)
        
        self.setLayout(self.layout)
        
        # Baseline coordinates state
        self.baseline_coords = None

        # Connect to layers events to automatically bind events on any points layers
        self.viewer.layers.events.inserted.connect(self._on_layer_inserted)
        
        # Connect already existing points layers
        for layer in self.viewer.layers:
            if isinstance(layer, napari.layers.Points):
                self.connect_points_layer(layer)

    def _on_layer_inserted(self, event):
        layer = event.value
        if isinstance(layer, napari.layers.Points):
            self.connect_points_layer(layer)

    def connect_points_layer(self, layer):
        if not isinstance(layer, napari.layers.Points):
            return
        if hasattr(layer, '_proofreader_connected') and layer._proofreader_connected:
            return
        layer._proofreader_connected = True
        
        # Make the color of newly added points different (yellow)
        layer.current_face_color = 'yellow'
        
        # Show the points in the 2D Z as they appear on all Z slices, even when out of focus
        layer.out_of_slice_display = True
        
        # Keep track of previous data to detect additions
        layer._prev_data = np.copy(layer.data)
        layer._updating_points = False
        
        def on_data_changed(event):
            if layer._updating_points:
                return
                
            current_data = layer.data
            prev_data = getattr(layer, '_prev_data', np.empty((0, 3)))
            
            # If points were added
            if len(current_data) > len(prev_data):
                # Find the image layer to perform snapping
                image_layer = None
                for l in self.viewer.layers:
                    if isinstance(l, napari.layers.Image):
                        image_layer = l
                        break
                        
                if image_layer is not None:
                    image_data = image_layer.data
                    scale = image_layer.scale if image_layer.scale is not None else (1.0, 1.0, 1.0)
                    
                    if len(image_data.shape) == 3:
                        depth, height, width = image_data.shape
                        scale_z, scale_y, scale_x = scale
                        
                        # Process the newly added point
                        idx = len(current_data) - 1
                        z_phys, y_phys, x_phys = current_data[idx]
                        
                        # Convert to pixel coords
                        z_pixel = np.clip(int(round(z_phys / scale_z)), 0, depth - 1)
                        y_pixel = np.clip(int(round(y_phys / scale_y)), 0, height - 1)
                        x_pixel = np.clip(int(round(x_phys / scale_x)), 0, width - 1)
                        
                        # Search in a 3D neighborhood around (z_pixel, y_pixel, x_pixel)
                        # Define half-radii for search window
                        r_z, r_y, r_x = 6, 12, 12
                        
                        z_start = max(0, z_pixel - r_z)
                        z_end = min(depth, z_pixel + r_z + 1)
                        y_start = max(0, y_pixel - r_y)
                        y_end = min(height, y_pixel + r_y + 1)
                        x_start = max(0, x_pixel - r_x)
                        x_end = min(width, x_pixel + r_x + 1)
                        
                        # Extract 3D subvolume crop
                        crop = image_data[z_start:z_end, y_start:y_end, x_start:x_end]
                        
                        # Find index of max intensity within the crop
                        flat_max_idx = np.argmax(crop)
                        z_max_local, y_max_local, x_max_local = np.unravel_index(flat_max_idx, crop.shape)
                        
                        # Map back to global voxel coordinates
                        z_max = z_start + z_max_local
                        y_max = y_start + y_max_local
                        x_max = x_start + x_max_local
                        
                        # Convert back to physical coordinates
                        z_phys_snapped = z_max * scale_z
                        y_phys_snapped = y_max * scale_y
                        x_phys_snapped = x_max * scale_x
                        
                        print(f"Snapped added point from ({z_phys:.2f}, {y_phys:.2f}, {x_phys:.2f}) "
                              f"to local peak ({z_phys_snapped:.2f}, {y_phys_snapped:.2f}, {x_phys_snapped:.2f}) "
                              f"voxel: ({z_max}, {y_max}, {x_max})")
                        
                        # --- REMOVE DUPLICATE POINTS ON NEARBY Z FOR THE SAME CELL ---
                        indices_to_keep = []
                        for i in range(len(prev_data)):
                            z_exist, y_exist, x_exist = prev_data[i]
                            # Calculate distance in voxels using scale spacing
                            dz = abs(z_exist - z_phys_snapped) / scale_z
                            dy = abs(y_exist - y_phys_snapped) / scale_y
                            dx = abs(x_exist - x_phys_snapped) / scale_x
                            
                            # If existing point is within cell radius, mark for removal
                            if dz <= 10 and dy <= 20 and dx <= 20:
                                print(f"Removing duplicate centroid on nearby Z/slice for the same cell structure: ({z_exist:.2f}, {y_exist:.2f}, {x_exist:.2f})")
                                continue
                            indices_to_keep.append(i)
                            
                        # Reconstruct coordinates array
                        kept_coords = prev_data[indices_to_keep]
                        new_coords = np.vstack([kept_coords, [z_phys_snapped, y_phys_snapped, x_phys_snapped]])
                        
                        # Apply updated coordinates
                        layer._updating_points = True
                        layer.data = new_coords
                        
                        # Reconstruct and apply color array
                        try:
                            old_colors = np.copy(layer.face_color)
                            kept_colors = old_colors[indices_to_keep]
                            new_colors = np.vstack([kept_colors, [1.0, 1.0, 0.0, 1.0]]) # Yellow color
                            layer.face_color = new_colors
                        except Exception as color_err:
                            print(f"Error slicing colors: {color_err}")
                            
                        layer._updating_points = False
                        
                        # Automatically update viewer dims slider to the snapped Z slice index so it is visible
                        try:
                            self.viewer.dims.set_current_step(0, int(z_max))
                        except Exception as dims_err:
                            print(f"Error updating viewer dims: {dims_err}")
            
            layer._prev_data = np.copy(layer.data)
            self.calculate_metrics()
            
        layer.events.data.connect(on_data_changed)
        
    def load_volume_dialog(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Open Volume TIFF File", "", "TIFF Files (*.tif *.tiff)")
        if filepath:
            self.start_loading_thread(filepath, "volume")
                
    def load_centroids_dialog(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Open SWC Centroids File", "", "SWC Files (*.swc)")
        if filepath:
            self.start_loading_thread(filepath, "centroids")

    def load_baseline_dialog(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Open Baseline Ground Truth SWC", "", "SWC Files (*.swc)")
        if filepath:
            print(f"Loading baseline SWC for comparison: {filepath}")
            df = read_swc(filepath)
            if df is not None:
                self.baseline_coords = np.column_stack((df['z'].values, df['y'].values, df['x'].values))
                # Add baseline points to viewer for visualization
                name = "Baseline_Ground_Truth"
                for layer in list(self.viewer.layers):
                    if layer.name == name:
                        self.viewer.layers.remove(layer)
                self.viewer.add_points(
                    self.baseline_coords,
                    name=name,
                    size=self.spin_marker_size.value() * 1.2,
                    face_color='transparent',
                    edge_color='green',
                    border_color='green',
                    blending='translucent'
                )
                print(f"Loaded baseline with {len(self.baseline_coords)} points.")
                self.calculate_metrics()


    def start_loading_thread(self, filepath, file_type):
        self.lbl_progress.setText(f"Loading {file_type}...")
        self.progress_bar.setValue(0)
        self.btn_load_vol.setEnabled(False)
        self.btn_load_centroids.setEnabled(False)
        
        self.thread = QThread()
        self.worker = LoadingWorker(filepath, file_type)
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.on_loading_finished)
        self.worker.error.connect(self.on_loading_error)
        
        # Cleanup
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        
        self.thread.start()

    def on_loading_finished(self, data, file_type, name):
        self.btn_load_vol.setEnabled(True)
        self.btn_load_centroids.setEnabled(True)
        self.progress_bar.setValue(100)
        self.lbl_progress.setText("Status: Load finished!")
        
        if file_type == "volume":
            scale = (self.spin_z.value(), self.spin_y.value(), self.spin_x.value())
            self.viewer.add_image(data, name=name, scale=scale, blending='additive', colormap='gray')
            print(f"Volume loaded successfully as a new layer: {name}")
        elif file_type == "centroids":
            if data is not None:
                coords_phys = np.column_stack((data['z'].values, data['y'].values, data['x'].values))
                size_val = self.spin_marker_size.value()
                self.viewer.add_points(
                    coords_phys,
                    name=name,
                    size=size_val,
                    face_color='red',
                    border_color='white',
                    blending='translucent'
                )
                print(f"Loaded {len(coords_phys)} centroids into new layer: {name}")

    def on_loading_error(self, err_msg):
        self.btn_load_vol.setEnabled(True)
        self.btn_load_centroids.setEnabled(True)
        self.progress_bar.setValue(0)
        self.lbl_progress.setText("Status: Error during load!")
        print(f"Failed to load file: {err_msg}")

    def calculate_metrics(self, val=None):
        if self.baseline_coords is None:
            return
            
        # Get current edited coordinates from active or first Points layer
        centroids_layer = self.viewer.layers.selection.active
        if not isinstance(centroids_layer, napari.layers.Points):
            for layer in self.viewer.layers:
                if isinstance(layer, napari.layers.Points) and layer.name != "Baseline_Ground_Truth":
                    centroids_layer = layer
                    break
        
        if centroids_layer is None:
            self.lbl_metrics_stats.setText("TP: - | FP: - | FN: -<br>Precision: - | Recall: - | F1: -")
            return
            
        edited_coords = centroids_layer.data
        if len(edited_coords) == 0:
            tp, fp, fn = 0, 0, len(self.baseline_coords)
            precision, recall, f1 = 0.0, 0.0, 0.0
            self.lbl_metrics_stats.setText(f"TP: {tp} | FP: {fp} | FN: {fn}<br>Precision: {precision:.4f} | Recall: {recall:.4f} | F1: {f1:.4f}")
            return
            
        # Calculate True Positives, False Positives, False Negatives, and True Negatives
        # Using KDTree for fast physical coordinates distance matching
        from scipy.spatial import KDTree
        tolerance = self.spin_tolerance.value()
        
        baseline_tree = KDTree(self.baseline_coords)
        edited_tree = KDTree(edited_coords)
        
        # TP/FN calculation: find matches in edited coords for each baseline point
        # A baseline point is matched (TP) if there is an edited point within tolerance.
        matched_baselines = 0
        for pt in self.baseline_coords:
            dist, _ = edited_tree.query(pt)
            if dist <= tolerance:
                matched_baselines += 1
                
        tp = matched_baselines
        fn = len(self.baseline_coords) - tp
        
        # FP calculation: edited points that do not match any baseline point
        matched_edited = 0
        for pt in edited_coords:
            dist, _ = baseline_tree.query(pt)
            if dist <= tolerance:
                matched_edited += 1
        fp = len(edited_coords) - matched_edited
        
        # Precision & Recall & F-score
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        self.lbl_metrics_stats.setText(
            f"<b>Metrics (Tol: {tolerance} px):</b><br>"
            f"TP: {tp} | FP: {fp} | FN: {fn}<br>"
            f"Precision: {precision:.4f}<br>"
            f"Recall: {recall:.4f}<br>"
            f"F-score: {f_score:.4f}"
        )
        print(f"Metrics recalculated - TP: {tp}, FP: {fp}, FN: {fn}, Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f_score:.4f}")

    def update_voxel_spacing(self, val=None):
        self.progress_bar.setValue(20)
        self.lbl_progress.setText("Status: Updating voxel spacing...")
        
        scale = (self.spin_z.value(), self.spin_y.value(), self.spin_x.value())
        active_layer = self.viewer.layers.selection.active
        
        self.progress_bar.setValue(50)
        if isinstance(active_layer, napari.layers.Image):
            active_layer.scale = scale
            print(f"Dynamically updated spacing of active layer '{active_layer.name}' to {scale}")
        else:
            for layer in self.viewer.layers:
                if isinstance(layer, napari.layers.Image):
                    layer.scale = scale
            print(f"Updated spacing of all loaded Image layers to {scale}")
            
        self.progress_bar.setValue(100)
        self.lbl_progress.setText(f"Status: Spacing updated to {scale}")

    def update_marker_size(self, val):
        self.progress_bar.setValue(20)
        self.lbl_progress.setText("Status: Updating marker size...")
        
        self.progress_bar.setValue(60)
        for layer in self.viewer.layers:
            if isinstance(layer, napari.layers.Points):
                layer.size = val
        print(f"Updated marker size to {val} for all points layers")
        
        self.progress_bar.setValue(100)
        self.lbl_progress.setText(f"Status: Marker size updated to {val}")

    def save_edits_dialog(self):
        centroids_layer = self.viewer.layers.selection.active
        if not isinstance(centroids_layer, napari.layers.Points):
            for layer in self.viewer.layers:
                if isinstance(layer, napari.layers.Points) and layer.name != "Baseline_Ground_Truth":
                    centroids_layer = layer
                    break
        
        if centroids_layer is None:
            self.lbl_progress.setText("Status: Save error (No points layer)")
            self.progress_bar.setValue(0)
            print("Error: No Points layer found to save.")
            return
            
        filepath, _ = QFileDialog.getSaveFileName(self, "Save SWC Centroids As...", "centroids_DAPI_scaled_edited.swc", "SWC Files (*.swc)")
        if filepath:
            self.progress_bar.setValue(20)
            self.lbl_progress.setText("Status: Saving SWC edits...")
            
            coords = centroids_layer.data
            size_val = self.spin_marker_size.value()
            
            self.progress_bar.setValue(60)
            success = save_swc(filepath, coords, marker_size=size_val)
            
            if success:
                self.progress_bar.setValue(100)
                self.lbl_progress.setText("Status: Edits saved successfully!")
                print(f"Edits saved to: {filepath}")
                self.calculate_metrics()
            else:
                self.progress_bar.setValue(0)
                self.lbl_progress.setText("Status: Error saving SWC file!")

def main():
    # Setup paths
    workspace_root = r"c:\Users\banerjee\Desktop\um1_3d_volume"
    default_vol_path = os.path.join(workspace_root, "docker_cell_detection", "F0200_multichannel_cmle_ch03.tif")
    default_swc_path = os.path.join(workspace_root, "docker_cell_detection", "centroids_FP_scaled.swc")
    
    print("Initializing Napari viewer...")
    viewer = napari.Viewer()
    
    # Instantiate dock widget
    widget = ProofreaderDockWidget(viewer)
    viewer.window.add_dock_widget(widget, name="Centroid Proofreader", area="right")
    
    # Auto-load default volume if it exists
    if os.path.exists(default_vol_path):
        print(f"Auto-loading default volume: {default_vol_path}")
        try:
            vol = tifffile.imread(default_vol_path)
            scale = (0.5, 0.1102, 0.1102)
            viewer.add_image(vol, name=os.path.basename(default_vol_path), scale=scale, blending='additive', colormap='gray')
        except Exception as e:
            print(f"Failed to auto-load volume: {e}")
            
    # Auto-load default centroids if they exist
    if os.path.exists(default_swc_path):
        print(f"Auto-loading default centroids: {default_swc_path}")
        df = read_swc(default_swc_path)
        if df is not None:
            coords_phys = np.column_stack((df['z'].values, df['y'].values, df['x'].values))
            viewer.add_points(
                coords_phys,
                name="Centroids",
                size=5.0,
                face_color='red',
                border_color='white',
                blending='translucent'
            )
            
    # Run Napari
    print("Launching Napari...")
    napari.run()

if __name__ == '__main__':
    main()
