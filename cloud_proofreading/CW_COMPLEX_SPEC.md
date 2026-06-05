# Topological CW-Complex JSON Specification (.json)

In our pipeline, skeletal graphs and cell centroids can be stored as topological 1-dimensional CW-Complexes encoded in JSON format. This format perfectly preserves graph topology, enabling mathematically rigorous definitions of 0-cells (vertices) and 1-cells (edges).

## Structure
The JSON object contains two primary arrays: `"0-cells"` (vertices/nodes) and `"1-cells"` (edges/connections).

### `0-cells` (Vertices)
A list of dictionaries. Each dictionary represents a physical point in 3D space.
- `"id"` (integer/string): Unique identifier for the vertex.
- `"x"` (float): X coordinate.
- `"y"` (float): Y coordinate.
- `"z"` (float): Z coordinate.
- `"radius"` (float, optional): Radius of the structure.

### `1-cells` (Edges)
A list of dictionaries representing the connections between the `0-cells`.
- `"id"` (integer/string): Unique identifier for the edge.
- `"source"` (integer/string): The `"id"` of the starting `0-cell`.
- `"target"` (integer/string): The `"id"` of the ending `0-cell`.

## Example
```json
{
  "0-cells": [
    { "id": 1, "x": 100.5, "y": 200.1, "z": 50.0, "radius": 5.0 },
    { "id": 2, "x": 105.0, "y": 205.0, "z": 51.0, "radius": 1.0 },
    { "id": 3, "x": 110.0, "y": 210.0, "z": 52.0, "radius": 1.0 }
  ],
  "1-cells": [
    { "id": 101, "source": 1, "target": 2 },
    { "id": 102, "source": 2, "target": 3 }
  ]
}
```
