# 3D Centroid Proofreading Tool

> **Created by: Samik Banerjee @ Mitralab @ Cold Spring Harbor Laboratory (CSHL)**

Interactive, cross-platform graphical tool built on Napari to visualize 3D cell volumes, overlay scaled SWC centroids, adjust rendering scaling dynamically, proofread (add/delete) centroids, and save results back to standardized formats.

---

## 🚀 Features

- **Double-Click Start**: Automatic dependency installation and app launch.
- **Cross-Platform**: Support for Windows (`.bat`), macOS, and Linux (`.sh`).
- **Smooth GUI Sidebar Controls**:
  - **Upload Volume**: Load massive 3D `.tif` volumes as dynamic, separate visual layers.
  - **Upload Centroids**: Layer DAPI or functional `.swc` coordinates onto the active viewer.
  - **Voxel Spacing (Z, Y, X)**: Spinboxes to update spatial spacing scales dynamically in real-time.
  - **Marker Size**: Rescale points on the fly for custom visibility.
  - **Active Progress Bar & Status Panel**: Visual loading indicator keeping the interface non-blocking and highly responsive.
  - **Save Edits**: Instantly export corrected centroids to standardized SWC files.

### 🌟 Advanced Centroid Proofreading Enhancements
- **3D Local Neighborhood Peak Snapping**: Click anywhere near a cell structure to place a centroid, and the tool will automatically search a 3D window of size `(13, 25, 25)` voxels ($\pm 6$ Z-slices, $\pm 12$ Y/X pixels) and snap coordinates exactly to the absolute local peak intensity center in physical space.
- **Synchronized View Focus Tracking**: When a point is added and snapped, the Napari dims slider automatically scrolls to the snapped Z-depth slice so you can instantly verify the alignment without manual searching.
- **Dynamic Duplicate Centroid Cleanup**: Placing a point near a cell structure automatically scans, identifies, and removes any existing centroid on neighboring Z-slices for the same cell, maintaining exactly one clean marker per cell structure.
- **Global Multi-Z Visibility (Out-of-Slice Rendering)**: Out-of-focus centroids display as smaller translucent circles on neighboring slices. You can view all cell layers simultaneously in 2D slicing mode without markers disappearing as you navigate.
- **High-Contrast Color Indicators**: Newly added or adjusted centroids appear in bright **yellow**, distinct from the original preloaded centroids in **red**, providing immediate visual feedback of edits.

---

## 🏃 Quick Start Guide

Ensure you have [Python 3.x](https://www.python.org/) installed.

### Windows (Double-Click Execution)
Double-click the startup batch script in this folder:
```bash
run_proofreader.bat
```

### macOS / Linux (Terminal Launch)
Open a terminal inside this directory and execute the shell script:
```bash
./run_proofreader.sh
```

---

## 🎯 How to Add Points & Snap to the Nearest Cell

To add a centroid point so that it perfectly catches and snaps to the nearest cell, follow this high-precision workflow:

1. **Select the Points Layer**:
   - In the Napari layer list on the left side of the window, click on the **Centroids** layer (or **Cell Centroids** layer in the standalone viewer) to make it active.
2. **Activate the Add Points Tool**:
   - Click the **Add points** icon in the layer controls panel (a circle icon with a `+` symbol in the top-left area), or simply press the shortcut key **`2`** on your keyboard.
3. **Click Near the Target Cell**:
   - Scroll the Z-slider to a slice where the target cell is visible.
   - Click **anywhere inside or close to the target cell boundaries**. You do *not* have to click exactly on the center pixel, nor do you have to find the single brightest Z-slice yourself.
4. **Snapping Engine Execution**:
   - **3D Peak Snapping**: The tool immediately scans a tight 3D box of size `(13, 25, 25)` voxels around your click, extracts the local peak intensity, and snaps the marker's coordinate to the true physical center of the cell.
   - **Auto-slice Focusing**: The Napari dimensions slider automatically scrolls to jump directly to the snapped $Z$ slice so you can instantly verify the alignment.
   - **Yellow Highlight**: Your newly added point will immediately render in **yellow** for visual distinction.
   - **Smart Duplicate Removal**: If there was already a marker on a nearby slice for this cell structure, the tool will automatically delete it to keep your datasets perfectly clean with one centroid per cell!

---

## 📝 Centroid Editing Workflow

1. Click **Upload Volume (.tif)** to import your 3D cell volume.
2. Click **Upload Centroids (.swc)** to overlay coordinates.
3. Use the **Voxel Spacing (Z, Y, X)** inputs to adjust scaling dimensions in real-time (Default: `0.5`, `0.1102`, `0.1102`).
4. **Modify Markers**:
   - Change marker size using the **Marker Size** control box.
   - Select the Centroids points layer on the left side of Napari.
   - Click the **Add points** button (or press `2` on your keyboard) to add new markers on selected voxels. The tool will automatically snap it in 3D, center the slider view, and delete any pre-existing duplicate markers on neighboring slices.
   - Select points using the **Select points** tool (or press `3`) and press `Delete` to remove bad/false centroids.
5. Click **Save Edits** to save the updated SWC coordinate matrix.
