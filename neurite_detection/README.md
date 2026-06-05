# Neurite Detection Pipeline

This directory contains a fast, memory-optimized, GPU-accelerated pipeline for extracting neurites from 3D microscopy volumes and converting them into a topological CW Complex graph format. It also includes an interactive Napari viewer for proofreading the extracted structures.

## System Requirements
- Python 3.9+
- `cupy` (for GPU acceleration)
- `sknw` (for graph extraction)
- `scikit-image`
- `napari`

## Modules

### 1. `process_neurites.py`
High-speed GPU-accelerated Frangi vesselness filter with **Hysteresis Thresholding**. It splits massive 3D TIFFs into overlapping memory chunks, performs the neurite enhancement, hysteresis propagation, and morphological closing entirely on the GPU via CuPy, and reconstructs the boolean mask.
- **Time Complexity**: $O(N \times S)$ where $N$ is the number of voxels, and $S$ is the number of multiscale filter sizes (sigmas).

### 2. `detect_somas.py`
GPU-accelerated soma boundary detection. It processes the full volume in 3D chunks, filters for thick cell bodies, and assigns unique integer IDs to each detected soma.

### 3. `cw_extraction.py`
Converts the 3D binary mask into an explicit 1D topological graph representation.
- **Soma Carving**: It subtracts detected soma volumes from the neurite mask to guarantee neurites terminate exactly at the cell body walls.
- **Topology Mapping**: Connected neurite sub-graphs are topologically traced and mapped to their adjoining somas. Unconnected structures are tracked as orphans.
- **CW Complex Generation**: It records graph nodes (0-cells), paths (1-cells), tube surfaces and soma bounding boxes (2-cells), and voxel volumes (3-cells) into a complete JSON specification.
- **Time Complexity**: Skeletonization takes $O(N)$ operations on the binary mask, and graph extraction via SKNW takes $O(P)$ where $P$ is the number of resulting skeleton pixels.

### 4. `viewer.py`
A specialized Napari-based proofreading tool that loads the original raw image alongside the extracted topological graph and 3D soma labels. It features **Automatic Structural Coloring**, where neurite components are dynamically colored to match their corresponding parent soma cell body for intuitive review.

## How to Run

You can run the entire pipeline at once using the master script:

```bash
cd neurite_detection
python run_pipeline.py --input "path/to/your/image.tif" --outdir "output"
```

The script will:
1. Detect neurites on the GPU.
2. Detect 3D somas on the GPU.
3. Carve somas, extract the skeleton, map component topologies, and build `cw_complex.json`.
4. Launch the Napari proofreading viewer automatically.

### Proofreading
- In Napari, select the `0-Cells (Nodes)` layer to add/move/delete junctions and endpoints.
- Select the `1-Cells (Edges)` layer to modify the paths.
- Press **`S`** to overwrite and save your edits back into the `cw_complex.json` file.
