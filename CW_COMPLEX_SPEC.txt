# 1D CW-Complex JSON Specification

This document rigidly defines the serialized spatial architecture explicitly evaluated inside the mathematical trace JSON outputs.

## Schema Overview: `cw_complex.json`

The topological bounds evaluate specifically to isolated features mapping distinct graph network elements natively:

```json
{
  "network_type": "1D CW Complex Forest",
  "cells_0_nodes": [ ... ],
  "cells_1_linestrings": [ ... ]
}
```

### 1. The 0-Cells (`cells_0_nodes`)
Encodes mathematical dimensionless vertices restricting boundaries.
*   **`node_id`** (Integer): Unique tracking abstraction.
*   **`type`** (String): Explicitly defined as `"boundary"` (terminal geometric endpoint) or `"junction"` (structural intersection linking multiple linestrings).
*   **`coord`** (Array `[Y, X]`): Raw spatial matrix layout indices natively defining Euclidean space mapping physically.

### 2. The 1-Cells (`cells_1_linestrings`)
Encodes continuous distinct spatial array traces connecting EXACTLY two 0-cells mathematically, guaranteeing **no sub-junctions internally bifurcate the sequence**.
*   **`line_id`** (Integer): A serialized identification array mapping sequences.
*   **`endpoints`** (Object): Contains `"source_id"` and `"target_id"` constraints anchoring physical geometry strictly identifying exactly two 0-Cells physically framing the layout.
*   **`geometry`** (Array of `[Y, X]` Arrays): Natively sequentially logs every micro-discrete raw spatial target along the structural string trace forming the curve natively across matrices.
*   **`forest_relation`** (Object): Contains a `"connects"` array (e.g., `["boundary", "junction"]`) capturing abstract relational boundary types connecting the string structurally.

---

# CW Graph Toolkit: Usage README

The `cw_graph_tools/` mathematical engine completely bypasses MATLAB built-in limitations. It structures and mutates geometric configurations rigorously mapping raw logic constraints dynamically against the JSON.

### Core Serialization Matrix
*   **`load_cw_json(json_path)`**: Reconstructs JSON representations into natively evaluated spatial structures immediately.
*   **`save_cw_json(cw_json, out_path)`**: Reverses abstractions mapping natively edited bounds securely onto `.json` architectures directly evaluating physical properties natively!

### Visualization Override
*   **`plot_cw_complex(cw_json)`**: Replaces arbitrary mathematical graphs and natively sketches explicit pure physical dimensions! Utilizing **piecewise cubic spline parametric mapping (`pchip`)**, it eliminates structural pixel serialization mapping sweeping curves matching Euclidean limits smoothly across bounds dynamically overriding discrete arrays. It labels boundaries with `Red Triangles` and intersections with `Blue Circles`.

### Topographical Isolation Scripts (Pure Array Logic)
*   **`find_mst(cw_json)`**: Uses a strictly native formulation of **Kruskal's Disjoint-Set Union** evaluated entirely mapping edge `geometry` integration curve lengths sequentially. Bypasses abstractions logically guaranteeing a minimal topological physical layout!
*   **`find_loops(cw_json)`**: Native pure sequence tracking array using explicit **Depth First Search (DFS)** isolating back-edges inherently mathematically isolating unbroken ring topologies.

### Geometric Matrix Editing Tools
*   **`delete_tree(cw_json, target_node_id)`**: Formulates an iterative **Breadth First Search (BFS)** culling array branches isolating exact connections spanning a queried network node completely cleanly.
*   **`add_tree(base_json, new_json)`**: Sequentially mathematically unions separated network sequences isolating boundary offset limits perfectly dynamically preventing duplicate mapping overlapping natively.
*   **`edit_cw_json(cw_json, op, ...)`**: A wrapper allowing isolated node and subset tracking overriding explicit graph properties logically over sequences:
    *   `op = 'add_node', node_id, type, coord`
    *   `op = 'add_edge', src_id, tgt_id, geometry, line_id`
    *   `op = 'delete_node', node_id` 
    *   `op = 'delete_edge', line_id`
