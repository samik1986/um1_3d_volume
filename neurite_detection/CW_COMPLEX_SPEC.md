# CW Complex Specification

This document outlines the JSON schema used to mathematically represent the topological structure of the 3D neurite network and associated cell bodies (somas) extracted by the pipeline.

The format uses a hierarchical topological representation known as a CW Complex, which breaks the geometry down into 0-cells (points), 1-cells (curves), 2-cells (surfaces), and 3-cells (volumes).

## Base Structure

```json
{
  "network_type": "1D/2D/3D CW Complex Forest",
  "cells_0_nodes": [],
  "cells_1_linestrings": [],
  "cells_2_surfaces": [],
  "cells_3_volumes": []
}
```

---

## `cells_0_nodes` (0-Cells)
Represents discrete points in space. In a skeletal network, these are the junction points where branches meet, or boundary endpoints where branches terminate.

*   `node_id` (int): Unique identifier for the node.
*   `type` (string): Either `"junction"` or `"boundary"`.
*   `coord` (array): The 3D coordinate `[Z, Y, X]` in pixel space.

---

## `cells_1_linestrings` (1-Cells)
Represents the 1D mathematical curves tracing the centerlines of the neurites.

*   `line_id` (int): Unique identifier for the curve.
*   `component_id` (int): The connected component identifier. If the neurite physically stems from a detected soma, this matches the integer `soma_id`. If it is unconnected (an orphan), it receives a unique negative integer.
*   `endpoints` (object): Contains `source_id` and `target_id` referring to the `node_id`s in `cells_0_nodes`.
*   `geometry` (array of arrays): A sequential list of `[Z, Y, X]` coordinates defining the high-resolution skeletal path.
*   `forest_relation` (object): Metadata indicating the node types at the endpoints (e.g., `{"connects": ["boundary", "junction"]}`).
*   `radius` (array): A list of radius values corresponding to each point in the `geometry`.

---

## `cells_2_surfaces` (2-Cells)
Represents the 2D boundary surfaces enclosing the 3D volumes. The pipeline generates two types of surfaces: tubular mesh specifications for the neurites, and bounding box specifications for the somas.

**For Neurites:**
*   `surface_id` (int): Matches the `line_id`.
*   `parent_line_id` (int): The 1-cell this surface encloses.
*   `geometry` (object): Type `"tube"` containing the `path` and `radii`.

**For Somas:**
*   `surface_id` (int): Unique ID offset (e.g., `1000000 + soma_id`).
*   `soma_id` (int): The integer ID of the soma detected in the 3D labels mask.
*   `geometry` (object): Type `"bounding_box"` containing `bounds: [z_min, z_max, y_min, y_max, x_min, x_max]`.

---

## `cells_3_volumes` (3-Cells)
Represents the physical 3D spaces occupied by the biological structures.

**For Neurites:**
*   `volume_id` (int): Matches the `line_id`.
*   `parent_line_id` (int): The 1-cell that resides inside this volume.
*   `volume_voxels` (int): The calculated volume in cubic pixels (based on $L \times \pi \times R^2$).

**For Somas:**
*   `volume_id` (int): Matches the `surface_id` offset.
*   `soma_id` (int): The integer ID of the soma.
*   `boundary_surface_id` (int): Reference to the 2-cell bounding box.
*   `volume_voxels` (int): The exact physical count of voxels belonging to the soma cell body.
