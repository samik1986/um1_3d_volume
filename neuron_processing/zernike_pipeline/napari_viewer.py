"""
napari_viewer.py

Author: Samik Banerjee
Date: May 2026
GitHub: https://github.com/samik1986/um1_3d_volume

Standalone Napari-based viewer for DAPI cell detection results
with interactive proofreading capabilities.

Features:
    - Memory-mapped volume loading
    - Cell centroids as Points layer
    - Cell labels overlay
    - Interactive proofreading dock widget (Approve, Delete, Split, Add)
    - 3D rendering with zoom/pan/rotate
    - Z-slice navigation in 2D mode
    - Export proofread results to JSON

Usage:
    python napari_viewer.py --volume output/dapi_cell_labels.tif \\
                            --labels output/dapi_cell_labels.tif \\
                            --centroids output/centroids.json \\
                            --cw output/cw_complex.json
"""

import os
import sys
import json
import time
import argparse
import numpy as np
import tifffile

# Add current directory for module imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from read_volume import load_volume, VOXEL_CONFIG


def load_centroids_from_json(path):
    """Load cell centroids from JSON file."""
    with open(path, 'r') as f:
        data = json.load(f)

    coords = []
    properties = {'id': [], 'radius_um': []}

    for cell in data:
        z = cell.get('z', 0)
        y = cell.get('y', 0)
        x = cell.get('x', 0)
        coords.append([z, y, x])
        properties['id'].append(cell.get('id', 0))
        properties['radius_um'].append(cell.get('radius_um', 0.0))

    return np.array(coords), properties


def load_cw_complex(path):
    """Load CW complex from JSON."""
    with open(path, 'r') as f:
        return json.load(f)


def build_edge_lines(cw_complex, centroid_coords, centroid_ids):
    """Build edge line data from CW complex 1D cells for Shapes layer."""
    if not cw_complex or 'cells_1d' not in cw_complex:
        return []

    # Build ID-to-index map
    id_to_idx = {cid: i for i, cid in enumerate(centroid_ids)}

    lines = []
    for edge in cw_complex['cells_1d']:
        a_id, b_id = edge['endpoints']
        if a_id in id_to_idx and b_id in id_to_idx:
            a_coord = centroid_coords[id_to_idx[a_id]]
            b_coord = centroid_coords[id_to_idx[b_id]]
            lines.append(np.array([a_coord, b_coord]))

    return lines


class ProofreadState:
    """Tracks proofreading edits in memory."""

    def __init__(self):
        self.edits = []
        self.deleted_ids = set()
        self.approved_ids = set()
        self.split_ids = set()
        self.add_count = 0
        self.move_count = 0

    def approve(self, cell_id, coords):
        self.approved_ids.add(cell_id)
        self.edits.append({
            'action': 'approve',
            'cell_id': int(cell_id),
            'coords': coords.tolist() if hasattr(coords, 'tolist') else list(coords),
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
        })
        return len(self.edits)

    def delete(self, cell_id, coords):
        self.deleted_ids.add(cell_id)
        self.edits.append({
            'action': 'delete',
            'cell_id': int(cell_id),
            'coords': coords.tolist() if hasattr(coords, 'tolist') else list(coords),
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
        })
        return len(self.edits)

    def split(self, cell_id, coords):
        self.split_ids.add(cell_id)
        self.edits.append({
            'action': 'split',
            'cell_id': int(cell_id),
            'coords': coords.tolist() if hasattr(coords, 'tolist') else list(coords),
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
        })
        return len(self.edits)

    def save(self, path):
        with open(path, 'w') as f:
            json.dump(self.edits, f, indent=2)
        print(f"[napari] Saved {len(self.edits)} edits to {path}")

    def summary(self):
        return (f"Edits: {len(self.edits)} total | "
                f"Approved: {len(self.approved_ids)} | "
                f"Deleted: {len(self.deleted_ids)} | "
                f"Split: {len(self.split_ids)} | "
                f"Added: {self.add_count} | Moved: {self.move_count}")


def create_proofread_widget(viewer, points_layer, labels_layer, proofread_state,
                             centroid_ids, output_dir, centroid_coords):
    """
    Create a Napari dock widget for proofreading.

    Uses magicgui for widget creation if available, otherwise
    falls back to a simple QWidget.
    """
    try:
        from magicgui import magicgui
        from magicgui.widgets import PushButton, Label, Container

        status_label = Label(value="Select a cell point to begin", name="status")
        info_label = Label(value="", name="cell_info")

        @magicgui(call_button="✓ Approve Selected")
        def approve_btn():
            _do_proofread_action('approve', viewer, points_layer, labels_layer,
                                 proofread_state, centroid_ids, status_label)

        @magicgui(call_button="✗ Delete Selected")
        def delete_btn():
            _do_proofread_action('delete', viewer, points_layer, labels_layer,
                                 proofread_state, centroid_ids, status_label)

        @magicgui(call_button="✄ Mark for Split")
        def split_btn():
            _do_proofread_action('split', viewer, points_layer, labels_layer,
                                 proofread_state, centroid_ids, status_label)

        @magicgui(call_button="💾 Save Edits")
        def save_btn():
            current_data = points_layer.data
            num_original = len(centroid_coords)
            
            # Check for moved points
            for i in range(num_original):
                if i < len(current_data):
                    # Check distance. If point shifted > 0.1 pixel
                    if np.linalg.norm(current_data[i] - centroid_coords[i]) > 0.1:
                        # Log it if not already marked deleted
                        if centroid_ids[i] not in proofread_state.deleted_ids:
                            proofread_state.edits.append({
                                'action': 'move',
                                'cell_id': int(centroid_ids[i]),
                                'old_coords': centroid_coords[i].tolist(),
                                'new_coords': current_data[i].tolist(),
                                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
                            })
                            proofread_state.move_count += 1
            
            # Check for added points
            if len(current_data) > num_original:
                for i in range(num_original, len(current_data)):
                    proofread_state.edits.append({
                        'action': 'add',
                        'coords': current_data[i].tolist(),
                        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
                    })
                    proofread_state.add_count += 1

            save_path = os.path.join(output_dir, "proofread_edits_napari.json")
            proofread_state.save(save_path)
            summary_label.value = proofread_state.summary()
            status_label.value = f"Saved to {os.path.basename(save_path)}"

        summary_label = Label(value=proofread_state.summary(), name="summary")

        container = Container(widgets=[
            status_label, info_label,
            approve_btn, delete_btn, split_btn, save_btn,
            summary_label,
        ], labels=False)

        viewer.window.add_dock_widget(container, name="Proofreading",
                                       area="right")

        # Connect selection callback
        @points_layer.mouse_drag_callbacks.append
        def on_click(layer, event):
            # Get selected point index
            if layer.selected_data:
                idx = list(layer.selected_data)[0]
                if idx < len(centroid_ids):
                    cid = centroid_ids[idx]
                    coords = layer.data[idx]
                    info_label.value = (
                        f"Cell {cid} | Z={coords[0]:.0f} Y={coords[1]:.0f} X={coords[2]:.0f}"
                    )
                    status_label.value = f"Selected cell {cid}"

        print("[napari] Proofreading widget created (magicgui)")

    except ImportError:
        print("[napari] magicgui not available, proofreading via console only")
        print("[napari] Install with: pip install magicgui")
        _setup_console_proofreading(viewer, points_layer, labels_layer,
                                     proofread_state, centroid_ids, output_dir)


def _do_proofread_action(action, viewer, points_layer, labels_layer,
                          proofread_state, centroid_ids, status_label):
    """Execute a proofreading action on the currently selected point."""
    if not points_layer.selected_data:
        status_label.value = "No cell selected!"
        return

    idx = list(points_layer.selected_data)[0]
    if idx >= len(centroid_ids):
        status_label.value = "Invalid selection"
        return

    cell_id = centroid_ids[idx]
    coords = points_layer.data[idx]

    if action == 'approve':
        count = proofread_state.approve(cell_id, coords)
        # Change point color to green
        colors = np.array(points_layer.face_color)
        colors[idx] = [0, 0.8, 0.3, 1.0]
        points_layer.face_color = colors
        status_label.value = f"✓ Approved cell {cell_id} ({count} edits)"

    elif action == 'delete':
        count = proofread_state.delete(cell_id, coords)
        # Remove point by setting size to 0 or removing from data
        sizes = np.array(points_layer.size)
        sizes[idx] = 0
        points_layer.size = sizes
        # Also clear the label in labels volume using a fast localized bounding box
        if labels_layer is not None:
            cz, cy, cx = map(int, coords)
            # Max cell radius is ~7um, which is ~14 pixels in Z and ~63 in X/Y. r=100 is extremely safe.
            r_z, r_xy = 30, 100
            z0, z1 = max(0, cz - r_z), min(labels_layer.data.shape[0], cz + r_z)
            y0, y1 = max(0, cy - r_xy), min(labels_layer.data.shape[1], cy + r_xy)
            x0, x1 = max(0, cx - r_xy), min(labels_layer.data.shape[2], cx + r_xy)
            
            subvol = labels_layer.data[z0:z1, y0:y1, x0:x1]
            subvol[subvol == cell_id] = 0
            labels_layer.refresh()
            
        status_label.value = f"✗ Deleted cell {cell_id} ({count} edits)"

    elif action == 'split':
        count = proofread_state.split(cell_id, coords)
        # Mark with yellow
        colors = np.array(points_layer.face_color)
        colors[idx] = [1.0, 0.8, 0.0, 1.0]
        points_layer.face_color = colors
        status_label.value = f"✄ Marked cell {cell_id} for split ({count} edits)"

    points_layer.refresh()


def _setup_console_proofreading(viewer, points_layer, labels_layer,
                                 proofread_state, centroid_ids, output_dir):
    """Fallback proofreading via console keybindings."""
    @viewer.bind_key('a')
    def approve_key(viewer):
        if points_layer.selected_data:
            idx = list(points_layer.selected_data)[0]
            if idx < len(centroid_ids):
                cid = centroid_ids[idx]
                proofread_state.approve(cid, points_layer.data[idx])
                print(f"[proofread] Approved cell {cid}")

    @viewer.bind_key('d')
    def delete_key(viewer):
        if points_layer.selected_data:
            idx = list(points_layer.selected_data)[0]
            if idx < len(centroid_ids):
                cid = centroid_ids[idx]
                proofread_state.delete(cid, points_layer.data[idx])
                sizes = np.array(points_layer.size)
                sizes[idx] = 0
                points_layer.size = sizes
                points_layer.refresh()
                print(f"[proofread] Deleted cell {cid}")

    @viewer.bind_key('s')
    def save_key(viewer):
        save_path = os.path.join(output_dir, "proofread_edits_napari.json")
        proofread_state.save(save_path)

    print("[napari] Console proofreading: A=Approve, D=Delete, S=Save")


def launch_napari_viewer(
    volume_path=None,
    labels_path=None,
    centroids_path=None,
    cw_path=None,
    output_dir="output",
    crop_to_labels=False,
):
    """
    Launch the Napari viewer with all layers and proofreading.

    Parameters
    ----------
    volume_path : str or None
        Path to raw DAPI TIFF volume.
    labels_path : str or None
        Path to cell labels TIFF.
    centroids_path : str or None
        Path to centroids JSON.
    cw_path : str or None
        Path to CW complex JSON.
    output_dir : str
        Output directory for proofread exports.
    """
    import napari

    print("[napari] Initializing DAPI Cell Viewer...")

    viewer = napari.Viewer(
        title="DAPI 3D Cell Viewer — Proofreading",
        ndisplay=3,
    )

    # Set voxel scale for all layers
    scale = [VOXEL_CONFIG.dz, VOXEL_CONFIG.dy, VOXEL_CONFIG.dx]

    # Load labels
    labels_layer = None
    labels_data = None
    crop_offset = None

    if labels_path and os.path.exists(labels_path):
        print(f"[napari] Loading labels: {labels_path}")
        labels_data = tifffile.imread(labels_path)
        
        if crop_to_labels:
            print("[napari] Cropping to non-zero labels...")
            nz = np.nonzero(labels_data)
            if len(nz[0]) > 0:
                zmin, zmax = nz[0].min(), nz[0].max() + 1
                ymin, ymax = nz[1].min(), nz[1].max() + 1
                xmin, xmax = nz[2].min(), nz[2].max() + 1
                
                # Add 10px padding around the bounding box
                zmin, zmax = max(0, zmin - 5), min(labels_data.shape[0], zmax + 5)
                ymin, ymax = max(0, ymin - 10), min(labels_data.shape[1], ymax + 10)
                xmin, xmax = max(0, xmin - 10), min(labels_data.shape[2], xmax + 10)
                
                print(f"[napari] Crop bbox: Z({zmin}:{zmax}) Y({ymin}:{ymax}) X({xmin}:{xmax})")
                labels_data = labels_data[zmin:zmax, ymin:ymax, xmin:xmax]
                crop_offset = np.array([zmin, ymin, xmin])
            else:
                print("[napari] Warning: Labels are empty, skipping crop.")

        labels_layer = viewer.add_labels(
            labels_data,
            name='Cell Labels',
            scale=scale,
            opacity=0.3,
        )

    # Load raw volume
    if volume_path and os.path.exists(volume_path):
        print(f"[napari] Loading volume: {volume_path}")
        vol = load_volume(volume_path, memmap=True)
        
        if crop_offset is not None:
            zmin, ymin, xmin = crop_offset
            zmax = zmin + labels_data.shape[0]
            ymax = ymin + labels_data.shape[1]
            xmax = xmin + labels_data.shape[2]
            vol = vol[zmin:zmax, ymin:ymax, xmin:xmax]
            
        mid_z = vol.shape[0] // 2
        viewer.add_image(
            vol,
            name='DAPI Raw',
            colormap='cyan',
            blending='additive',
            scale=scale,
            contrast_limits=[0, np.percentile(vol[mid_z], 99)],
        )
    else:
        print("[napari] No volume path provided, skipping raw image layer")

    # Load centroids
    points_layer = None
    centroid_ids = []
    centroid_coords = None

    if centroids_path and os.path.exists(centroids_path):
        print(f"[napari] Loading centroids: {centroids_path}")
        centroid_coords, centroid_props = load_centroids_from_json(centroids_path)
        centroid_ids = centroid_props['id']
        
        if crop_offset is not None:
            centroid_coords = centroid_coords - crop_offset

        # Size proportional to radius, but scaled much larger for visibility
        sizes = np.array(centroid_props['radius_um']) * 6

        points_layer = viewer.add_points(
            centroid_coords,
            name='Cell Centroids',
            face_color='red',
            size=sizes,
            scale=scale,
            properties=centroid_props,
            opacity=1.0,
            ndim=3,
        )

    # Load CW complex edges as Shapes layer
    if cw_path and os.path.exists(cw_path) and centroid_coords is not None:
        print(f"[napari] Loading CW complex: {cw_path}")
        cw = load_cw_complex(cw_path)

        edge_lines = build_edge_lines(cw, centroid_coords, centroid_ids)
        if edge_lines:
            viewer.add_shapes(
                edge_lines,
                shape_type='line',
                name='CW 1D Edges',
                edge_color='#7c5ad9',
                edge_width=0.8,
                scale=scale,
                opacity=0.4,
            )
            print(f"[napari] Added {len(edge_lines)} edges")

    # Setup proofreading
    proofread_state = ProofreadState()

    if points_layer:
        create_proofread_widget(
            viewer, points_layer, labels_layer,
            proofread_state, centroid_ids, output_dir, np.copy(centroid_coords)
        )

    print("[napari] Viewer ready! Use mouse to navigate (3D mode).")
    print("[napari] Click on cell centroids to select them for proofreading.")

    napari.run()

    # Auto-save on exit if there are unsaved edits
    if proofread_state.edits:
        save_path = os.path.join(output_dir, "proofread_edits_napari.json")
        proofread_state.save(save_path)


def main():
    parser = argparse.ArgumentParser(
        description="Napari DAPI Cell Viewer with Proofreading"
    )
    parser.add_argument('--volume', type=str, default=None,
                        help="Path to raw DAPI TIFF volume")
    parser.add_argument('--labels', type=str, default="output/dapi_cell_labels.tif",
                        help="Path to cell labels TIFF")
    parser.add_argument('--centroids', type=str, default="output/centroids.json",
                        help="Path to centroids JSON")
    parser.add_argument('--cw', type=str, default="output/cw_complex.json",
                        help="Path to CW complex JSON")
    parser.add_argument('--output-dir', type=str, default="output",
                        help="Output directory for proofread exports")
    parser.add_argument('--crop-to-labels', action='store_true',
                        help="Crop the raw volume and labels to the bounding box of the non-zero labels")
    args = parser.parse_args()

    launch_napari_viewer(
        volume_path=args.volume,
        labels_path=args.labels,
        centroids_path=args.centroids,
        cw_path=args.cw,
        output_dir=args.output_dir,
        crop_to_labels=args.crop_to_labels,
    )


if __name__ == "__main__":
    main()
