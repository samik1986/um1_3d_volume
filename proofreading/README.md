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

## 📝 Centroid Editing Workflow

1. Click **Upload Volume (.tif)** to import your 3D cell volume.
2. Click **Upload Centroids (.swc)** to overlay coordinates.
3. Use the **Voxel Spacing (Z, Y, X)** inputs to adjust scaling dimensions in real-time (Default: `0.5`, `0.1102`, `0.1102`).
4. **Modify Markers**:
   - Change marker size using the **Marker Size** control box.
   - Select the Centroids points layer on the left side of Napari.
   - Click the **Add points** button (or press `2` on your keyboard) to add new markers on selected voxels.
   - Select points using the **Select points** tool (or press `3`) and press `Delete` to remove bad/false centroids.
5. Click **Save Edits** to save the updated SWC coordinate matrix.
