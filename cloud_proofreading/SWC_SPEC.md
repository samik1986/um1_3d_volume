# SWC File Specification (.swc)

The `.swc` format is the standard neuroinformatics format for storing neuronal morphology (skeletons). 

## Structure
An SWC file is a plaintext file. Lines beginning with `#` are comments. Data lines contain exactly 7 space-separated numerical values representing a single node in the tree.

## Columns
1. **Node ID (integer):** A unique identifier for the node (usually starting from 1).
2. **Structure Identifier (integer):** The type of neuronal structure:
   - `0` = undefined
   - `1` = soma (cell body)
   - `2` = axon
   - `3` = basal dendrite
   - `4` = apical dendrite
   - `5`+ = custom 
3. **X Coordinate (float):** Spatial X position.
4. **Y Coordinate (float):** Spatial Z position (Note: in some viewers Y and Z are swapped).
5. **Z Coordinate (float):** Spatial Y position.
6. **Radius (float):** The radius of the neurite at this node. (In our topological graphs, this is often set to `1.0`).
7. **Parent ID (integer):** The Node ID of the parent node to which this node is connected. If the node is a root (e.g., the soma), the parent ID is `-1`.

## Example
```text
# NodeID StructureID X Y Z Radius ParentID
1 1 100.5 200.1 50.0 5.0 -1
2 3 105.0 205.0 51.0 1.0 1
3 3 110.0 210.0 52.0 1.0 2
```
