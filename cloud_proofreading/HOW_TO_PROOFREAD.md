# 📖 Cloud Proofreading Portal Guide

Welcome to the Cloud Proofreading Interface! This document explains how to securely log into the cloud server and use the interactive tools to validate machine-generated biological structures.

Depending on how your administrator has configured the server, you will be presented with one of two tools: the **Neurite Network Editor** or the **Cell Centroid Editor**.

---

## ☁️ 1. How to Access the Cloud Portal

This portal is designed to let you perform heavy 3D rendering and structural edits directly from your web browser without installing any software. The cloud server's physical NVIDIA GPU handles all the rendering and mathematically intense operations for you.

1. **Navigate to the Portal**: Open the secure URL provided by your administrator (e.g., `https://your-server-ip.nip.io`) in Google Chrome, Firefox, or Microsoft Edge.
2. **Authentication**: This portal is protected by **Google OAuth2**. You will be redirected to a standard "Sign in with Google" page. Enter your approved Google email address and password.
3. **The Interface**: Upon successful login, you will immediately see the Napari 3D interface streaming directly in your browser.

### General Browser Navigation Controls
- **Rotate 3D**: Click and drag the left mouse button anywhere in the black canvas.
- **Pan**: Hold `Shift` + click and drag.
- **Zoom**: Scroll your mouse wheel up and down.
- **Toggle Visibility**: Click the small "Eye" icon next to any layer in the bottom-left corner to hide or show it.

---

## 🧬 2. Using the Neurite Network Editor

If you are loaded into the **Neurite Network Editor**, you are correcting the topological CW Complex graph of neurite branches. 

### What You Will See
- **Raw Data Layer**: The original 3D TIFF image.
- **Somas Layer**: The 3D detected cell bodies.
- **0-Cells (Nodes)**: Branch points (junctions) and endpoints of the neurites (selectable dots).
- **1-Cells (Edges)**: Paths connecting the nodes (lines).
- *Unique Feature: Notice that the neurite paths are dynamically colored to exactly match the color of the soma they originate from!*

### Editing Nodes (Junctions & Endpoints)
You must use the `0-Cells (Nodes)` layer to add or remove structural points.
- Select the `0-Cells (Nodes)` layer in the bottom-left layer list.
- Click the **Add points** button (a circle with a plus) in the top-left toolbar to place new nodes in the 3D space.
- Click the **Select points** button (the arrow icon) to select an existing node. You can then press `Backspace` or `Delete` to remove the node, or drag it to move it.

### Editing Edges (Connections)
- Select the `1-Cells (Edges)` layer.
- Click the **Add shapes** button to draw a new connection between two nodes.
- Use the **Select shapes** button to highlight incorrect connections and press `Delete`.

### 🚀 Saving & Mathematical Edge Snapping
Once you are happy with your topological edits, ensure the viewer window is focused and press **`S`** on your keyboard.
- **Magic Edge Snapping Algorithm:** You do not need to trace paths perfectly when drawing edges! When you press `S`, the system automatically snaps the ends of your drawn edges to the nearest mathematically perfect neurite centerline (within a search radius of 8 pixels).
- The edits are seamlessly saved directly back to the `cw_complex.json` file on the server.

---

## 🔴 3. Using the Cell Centroid Proofreader

If you are loaded into the **Cell Centroid Proofreader**, you are correcting basic cell-counting coordinates stored in `.swc` files.

### What You Will See
- **Raw Image**: The 3D microscopy stack.
- **Centroids Layer**: A Napari Points layer containing small spheres, representing the mathematically calculated centers of the cells.

### Preparing the View
- Select the `Centroids` layer in the bottom-left panel so that the point editing tools appear in the toolbar.
- Ensure you are in **3D mode**. You can toggle between 2D slices and 3D volume rendering using the square button located at the very bottom left corner of the image canvas.

### Correcting False Positives (Deleting)
If the algorithm mistakenly detected a cell where there is none:
- Click the **Select points** tool (the arrow icon) in the top-left toolbar.
- Click the incorrect centroid sphere to highlight it.
- Press `Backspace` or `Delete` on your keyboard to remove it.

### Correcting False Negatives (Adding)
If the algorithm missed a cell:
- Click the **Add points** tool (the circle with a plus icon).
- Click in the 3D space directly on the center of the missed cell body to place a new centroid.

### Refining Localization (Moving)
If a centroid is slightly off-center:
- Use the **Select points** tool to click and hold the centroid.
- Drag the centroid to the precise correct location.

### 💾 Saving Your Progress
- Press **`S`** on your keyboard at any time. The system will instantly extract the updated 3D coordinates from the viewer and overwrite the `.swc` file on the server.
