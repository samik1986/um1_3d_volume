# 📖 How to Proofread

Welcome to the Cloud Proofreading Portal! This guide explains how to use the interactive tools to correct and validate the machine-generated biological structures.

Depending on the configuration of the server, you will be presented with one of two tools: the **Neurite Network Editor** or the **Cell Centroid Editor**.

---

## 🌐 Accessing the Cloud Portal
If your lab has deployed this on a cloud server:
1. Open your web browser and navigate to the secure URL provided by your administrator (e.g., `https://your-server-ip.nip.io`).
2. You will be prompted to "Sign in with Google".
3. Upon successful login, you will immediately see the Napari 3D interface streaming directly in your browser.

---

## 🧬 Tool 1: Neurite Network Editor (CW Complex)

This tool is used to correct the topological graph of neurite branches and cell bodies. 

### What You Will See
- **Raw Data Layer**: The original 3D TIFF image.
- **Somas Layer**: The 3D detected cell bodies.
- **0-Cells (Nodes)**: The branch points (junctions) and endpoints of the neurites, shown as dots.
- **1-Cells (Edges)**: The paths connecting the nodes, shown as lines.

*Feature: Neurites are dynamically colored to exactly match the color of the soma they originate from!*

### How to Edit

**1. Editing Nodes (Junctions & Endpoints)**
- Select the `0-Cells (Nodes)` layer in the bottom-left layer list.
- Click the **Add points** button (circle with a plus) in the top-left toolbar to place new nodes.
- Click the **Select points** button (arrow) to select an existing node. You can then press `Backspace` / `Delete` to remove it, or drag it to move it.

**2. Editing Edges (Connections)**
- Select the `1-Cells (Edges)` layer.
- Click the **Add shapes** button to draw new connections between nodes.
- Use the **Select shapes** button to delete incorrect connections.

**3. Saving & Mathematical Edge Snapping**
- Once you are happy with your edits, ensure the viewer window is focused and press **`S`** on your keyboard.
- **Magic Edge Snapping:** You do not need to trace paths perfectly! When you press `S`, the system will automatically snap the ends of your drawn edges to the nearest mathematically perfect neurite centerline. This guarantees your edits maintain strict physical and topological continuity.
- The edits are saved directly back to the `cw_complex.json` file on the server.

---

## 🔴 Tool 2: Cell Centroid Proofreader

This tool is used for simple cell-counting and localization, editing coordinates stored in `.swc` files.

### What You Will See
- **Raw Image**: The 3D microscopy stack.
- **Centroids Layer**: A Napari Points layer representing the calculated centers of the cells.

### How to Edit
- Select the `Centroids` layer.
- Ensure you are in 3D mode (the 2D/3D toggle button at the bottom left of the image canvas).
- Use the **Add points** tool to mark cell bodies that the algorithm missed. 
- Use the **Select points** tool to highlight false positives and press `Delete`.
- You can drag points to adjust their 3D coordinates.

### Saving
- Press **`S`** on your keyboard to instantly write your corrected coordinates back to the `.swc` file.

---

## ⌨️ General Napari Controls (Browser)
- **Rotate 3D**: Click and drag the left mouse button.
- **Pan**: Hold `Shift` + click and drag.
- **Zoom**: Scroll wheel.
- **Toggle Visibility**: Click the "Eye" icon next to any layer to hide/show it, helping you see the raw data underneath your edits.
