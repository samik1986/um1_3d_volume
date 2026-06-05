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
High-speed GPU-accelerated Frangi vesselness filter. It splits massive 3D TIFFs into overlapping memory chunks, performs the neurite enhancement and morphological closing entirely on the GPU via CuPy, and reconstructs the boolean mask.
- **Time Complexity**: $O(N \times S)$ where $N$ is the number of voxels, and $S$ is the number of multiscale filter sizes (sigmas).

### 2. `cw_extraction.py`
Converts the 3D binary mask into an explicit 1D topological graph representation according to the `CW_COMPLEX_SPEC.md` specification. It records graph nodes (0-cells) and paths (1-cells).
- **Time Complexity**: Skeletonization takes $O(N)$ operations on the binary mask, and graph extraction via SKNW takes $O(P)$ where $P$ is the number of resulting skeleton pixels.

### 3. `viewer.py`
A specialized Napari-based proofreading tool that loads the original raw image alongside the extracted topological graph. It renders junctions and endpoints as editable points and paths as editable lines.

## How to Run

You can run the entire pipeline at once using the master script:

```bash
cd neurite_detection
python run_pipeline.py --input "path/to/your/image.tif" --outdir "output"
```

The script will:
1. Detect neurites on the GPU.
2. Extract the skeleton and build `cw_complex.json`.
3. Launch the Napari proofreading viewer automatically.

### Proofreading
- In Napari, select the `0-Cells (Nodes)` layer to add/move/delete junctions and endpoints.
- Select the `1-Cells (Edges)` layer to modify the paths.
- Press **`S`** to overwrite and save your edits back into the `cw_complex.json` file.
