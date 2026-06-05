# Topological CW-Complex JSON Specification (.json)

In our pipeline, skeletal graphs, cell centroids, and volume meshes can be stored as topological CW-Complexes encoded in JSON format. This format perfectly preserves graph and mesh topology, enabling mathematically rigorous definitions of 0-cells (vertices), 1-cells (edges), 2-cells (faces), and 3-cells (volumes).

## Structure
The JSON object contains primary arrays for each topological dimension: `"0-cells"`, `"1-cells"`, `"2-cells"`, and `"3-cells"`.

### `0-cells` (Vertices / Nodes)
A list of dictionaries. Each dictionary represents a physical point in 3D space.
- `"id"` (integer/string): Unique identifier for the vertex.
- `"x"` (float): X coordinate.
- `"y"` (float): Y coordinate.
- `"z"` (float): Z coordinate.
- `"radius"` (float, optional): Radius of the structure.

### `1-cells` (Edges / Connections)
A list of dictionaries representing the connections (lines) bounded by `0-cells`.
- `"id"` (integer/string): Unique identifier for the edge.
- `"source"` (integer/string): The `"id"` of the starting `0-cell`.
- `"target"` (integer/string): The `"id"` of the ending `0-cell`.

### `2-cells` (Faces / Surfaces)
A list of dictionaries representing 2D surfaces bounded by lower-dimensional cells.
- `"id"` (integer/string): Unique identifier for the face.
- `"boundary"` (array): An ordered list of `"id"`s representing the boundary. This can be a list of `0-cells` (vertices forming a polygon) or `1-cells` (edges forming the loop).

### `3-cells` (Volumes / Polyhedra)
A list of dictionaries representing 3D solid volumes bounded by `2-cells`.
- `"id"` (integer/string): Unique identifier for the volume.
- `"boundary"` (array): A list of `"id"`s corresponding to the `2-cells` (faces) that completely enclose the volume.

## Example
```json
{
  "0-cells": [
    { "id": 1, "x": 100.5, "y": 200.1, "z": 50.0, "radius": 5.0 },
    { "id": 2, "x": 105.0, "y": 205.0, "z": 51.0, "radius": 1.0 },
    { "id": 3, "x": 110.0, "y": 210.0, "z": 52.0, "radius": 1.0 },
    { "id": 4, "x": 105.0, "y": 215.0, "z": 55.0, "radius": 1.0 }
  ],
  "1-cells": [
    { "id": 101, "source": 1, "target": 2 },
    { "id": 102, "source": 2, "target": 3 },
    { "id": 103, "source": 3, "target": 1 }
  ],
  "2-cells": [
    { "id": 201, "boundary": [1, 2, 3] },
    { "id": 202, "boundary": [1, 2, 4] },
    { "id": 203, "boundary": [2, 3, 4] },
    { "id": 204, "boundary": [3, 1, 4] }
  ],
  "3-cells": [
    { "id": 301, "boundary": [201, 202, 203, 204] }
  ]
}
```
