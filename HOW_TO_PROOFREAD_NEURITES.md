# 🧬 How to Proofread: Neurite Network Editor

This guide explains how to use the **Neurite Network Editor** to correct the topological graph of neurite branches and cell bodies. 

This editor relies on a mathematically defined **CW Complex**, breaking the neuron structure down into 0-cells (points/junctions) and 1-cells (paths/edges).

---

## What You Will See
When you launch the viewer, the left-hand panel will display several layers:
- **Raw Data Layer**: The original 3D TIFF image.
- **Somas Layer**: The 3D detected cell bodies.
- **0-Cells (Nodes)**: The branch points (junctions) and endpoints of the neurites, shown as selectable dots.
- **1-Cells (Edges)**: The paths connecting the nodes, shown as lines.

*Unique Feature: Notice that the neurite paths are dynamically colored to exactly match the color of the soma they originate from!*

---

## Editing Tools

### 1. Editing Nodes (Junctions & Endpoints)
You must use the `0-Cells (Nodes)` layer to add or remove structural points.
- Select the `0-Cells (Nodes)` layer in the bottom-left layer list.
- Click the **Add points** button (a circle with a plus) in the top-left toolbar to place new nodes in the 3D space.
- Click the **Select points** button (the arrow icon) to select an existing node. 
- You can then press `Backspace` or `Delete` to remove the node, or drag it to move it.

### 2. Editing Edges (Connections)
Once your nodes are correctly placed, you can define how they connect.
- Select the `1-Cells (Edges)` layer.
- Click the **Add shapes** button to draw a new connection between two nodes.
- Use the **Select shapes** button to highlight incorrect connections and press `Delete`.

---

## 🚀 Saving & Mathematical Edge Snapping

Once you are happy with your topological edits, ensure the viewer window is focused and press **`S`** on your keyboard.

**Magic Edge Snapping Algorithm:** 
You do not need to trace paths perfectly when drawing edges! When you press `S`, the system engages a mathematical snapping algorithm:
1. It analyzes the mathematical skeleton of the neurites.
2. It automatically snaps the ends of your drawn edges to the nearest mathematically perfect neurite centerline (within a search radius of 8 pixels).
3. This guarantees your manual edits maintain strict physical and topological continuity without requiring pixel-perfect hand-tracing.

The edits are seamlessly saved directly back to the `cw_complex.json` file on the server.
