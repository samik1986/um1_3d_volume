# 🔴 How to Proofread: Cell Centroids

This guide explains how to use the **Cell Centroid Proofreader** to correct basic cell-counting and localization. This tool is specifically designed to edit coordinate data stored in standard `.swc` files.

---

## What You Will See
When you launch the viewer, the left-hand panel will display two layers:
- **Raw Image**: The 3D microscopy stack.
- **Centroids Layer**: A Napari Points layer containing hundreds of small spheres, representing the mathematically calculated centers of the cells.

---

## Editing Tools

### 1. Preparing the View
- Select the `Centroids` layer in the bottom-left panel so that the point editing tools appear in the toolbar.
- Ensure you are in **3D mode**. You can toggle between 2D slices and 3D volume rendering using the square button located at the very bottom left corner of the image canvas.

### 2. Correcting False Positives (Deleting)
If the algorithm mistakenly detected a cell where there is none:
- Click the **Select points** tool (the arrow icon) in the top-left toolbar.
- Click the incorrect centroid sphere to highlight it.
- Press `Backspace` or `Delete` on your keyboard to remove it.

### 3. Correcting False Negatives (Adding)
If the algorithm missed a cell:
- Click the **Add points** tool (the circle with a plus icon).
- Click in the 3D space directly on the center of the missed cell body to place a new centroid.

### 4. Refining Localization (Moving)
If a centroid is slightly off-center:
- Use the **Select points** tool to click and hold the centroid.
- Drag the centroid to the precise correct location.

---

## 💾 Saving Your Progress

- Press **`S`** on your keyboard at any time.
- The system will instantly extract the updated 3D coordinates from the viewer and overwrite the `.swc` file on the server.
