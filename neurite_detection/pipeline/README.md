# Single-Channel Neurite & Soma Extraction Pipeline

A highly optimized, GPU-accelerated pipeline built to extract massively scaled 3D Somas and Neurite Skeletons strictly from a single massive `488` image volume. 

The pipeline handles dense, noisy volumes by automatically slicing the array into parallel chunks, filtering high/low frequency artifacts on the GPU with CuPy, calculating the Somas, and explicitly subtracting them to generate pristine skeletonizations with multi-threaded CPU evaluation.

## Architecture & Logic

1. **`core/cell_detection.py` (Soma Extraction)**: Isolates 3D somas across massive volumes. It utilizes Gaussian high/low frequency smoothing and percentile-based filtering on CuPy arrays to locate dense soma clusters. It explicitly uses **heavy morphological opening (erosions + dilations)** to completely sever any thick tubular dendrites attached to the somas, leaving perfectly isolated cell bodies.
2. **`core/neurite_detection.py` (Skeletonization)**: Uses a highly parallelized **Analytical 3D Frangi Vesselness** filter on CuPy with a safe `gpu_semaphore=1` constraint to avoid PCIe thrashing. It is specially tuned to extract **thick, bright tubular dendrites** (`sigmas=[2.0, 4.0]`, `thresh=0.05`) while aggressively ignoring thin, faint noise and small disconnected fragments. The somas are carefully subtracted from this mask post-Frangi filtering, before deploying an ultra-fast **chunked, multi-threaded `skimage` topological skeletonization** across 8 CPU cores.
3. **`core/graph_export.py` (Graph Exporting)**: Merges the datasets! It exports the `488` Somas as explicit isolated centroids (Node Type `2`) and the Neurite Skeletons (Node Type `3`) directly into unified JSON (CW-Complex) and SWC formats, scaled to absolute physical coordinates.
4. **`visualization/proofreader.py` (Interactive Proofreading)**: A lightweight Napari interface tailored for editing massive datasets. Features intensity snapping and real-time disk saving.

## Getting Started

You only need to supply your target TIFF file. The wrapper scripts will automatically install all Python dependencies via `pip` and derive a prefix from your filename to organize your outputs.

### Run the Pipeline
For Windows:
```powershell
.\run_pipeline.bat --input_file "path/to/your/488_channel.tif" --output_dir "pipeline_output" --visualize
```

For Linux / Mac:
```bash
./run_pipeline.sh --input_file "path/to/your/488_channel.tif" --output_dir "pipeline_output" --visualize
```

### Advanced Overrides
- **Custom Thresholds**: You can manually override the Otsu cutoff thresholds for either step:
  - `--thresh_488 1200.5` (Tunes the strictness of the neurite extraction)
  - `--thresh_488_soma 95.0` (Tunes the percentile cutoff for the soma extraction)
- **Physical Scaling**: Override the hardcoded voxel resolution for the JSON/SWC graph exports:
  - `--scale_x 0.2 --scale_y 0.2 --scale_z 1.0`
- **Output Naming**: If you don't want the pipeline to inherit the native filename prefix:
  - `--out_prefix "Sample_A"`
- **Hardware Fallback**: If your VRAM is completely overwhelmed, append `--disable_gpu` to fall back entirely to CPU computation.
## Input Specifications

The pipeline strictly expects a **single-channel 3D TIFF** volume representing the fluorescent neurite channel (e.g., 488nm).
- **Dimensions**: Z, Y, X (Standard TIFF stack).
- **Scale**: The data should be isotropic or scaled in memory. If the Z-axis scaling differs from X/Y, ensure you provide the `--scale_z`, `--scale_x`, and `--scale_y` overrides when running the pipeline so the physical outputs are stretched correctly.

## Output Specifications

The pipeline automatically creates an output directory and populates it with the following dataset formats:

1. **Boolean Numpy Masks (`.npy`)**:
   - `[prefix]_soma_mask_488.npy`: A 3D boolean volume of the dense cell bodies.
   - `[prefix]_neurite_mask_488.npy`: A 3D boolean volume of the thick volumetric dendrites.
   - `[prefix]_skeleton_mask_488.npy`: A 3D boolean volume of the 1-pixel wide morphological skeleton paths.
2. **SWC Files (`.swc`)**:
   - `[prefix]_skeletons.swc`: The raw voxel-coordinate topological graph.
   - `[prefix]_skeletons_micrometers.swc`: The physical graph scaled by the XYZ resolution parameters.
3. **CW-Complex JSON (`.json`)**:
   - `[prefix]_cw_complex.json`: The raw voxel-coordinate graph structured with vertices and edges.
   - `[prefix]_cw_complex_micrometers.json`: The physically scaled JSON graph.


## Visualization

The pipeline provides two powerful visualization tools built on Napari.

### 1. The Flexible Visualizer
If you want to view arbitrary sets of files, you can use the standalone `flex_visualizer.py`. It dynamically inspects file extensions and loads them into their optimal Napari layers simultaneously:
```bash
python pipeline/visualization/flex_visualizer.py raw_image.tif soma_mask.npy neurite_mask.npy skeletons.swc skeletons.json
```
- `.tif` -> Loaded as lazily memory-mapped 3D Volumes
- `.npy` -> Loaded as semi-transparent 3D Labels (if masks)
- `.swc` -> Loaded as 3D Line Shapes
- `.json` (CW Complex) -> Loaded as 3D Points (Nodes) and 3D Paths (Edges)

### 2. The Interactive Proofreader
If you utilize the `--visualize` flag when running the pipeline, it will automatically launch the Interactive Proofreader immediately after generation. 

#### Hotkeys
- **Snap to Intensity (F)**: Select any skeleton shape with the Napari Vertex tool and press `F`. The script will search the local 3D neighborhood of the raw image and automatically snap every vertex of your selected skeleton precisely to the maximum fluorescent intensity peak!
- **Save Edits (S)**: Press `S` to instantly overwrite the `cw_complex.json` file with your modified graphs.

