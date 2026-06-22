# Multi-Channel Neurite, Soma & Barcode Extraction Pipeline

A highly optimized, GPU-accelerated pipeline built to extract 3D Somas, Neurite Skeletons, and Barcodes from multi-channel image volumes. 

The pipeline handles dense, noisy volumes by automatically slicing the array into parallel chunks, filtering high/low frequency artifacts on the GPU with CuPy, calculating the Somas, and explicitly subtracting them to generate pristine skeletonizations with multi-threaded CPU evaluation. It also identifies barcodes in the 555 and 640 channels and structurally filters them against the neurite manifolds.

## Architecture & Logic

1. **`core/cell_detection.py` (Soma Extraction)**: Isolates 3D somas across massive volumes using GPU-accelerated Gaussian filtering and percentile thresholds. Uses morphological operations to sever thick dendrites, leaving isolated cell bodies. Operations are optimized in `float32` to prevent memory blowouts on massive volumes.
2. **`core/neurite_detection.py` (Skeletonization)**: Uses a highly parallelized **Analytical 3D Frangi Vesselness** filter on CuPy to extract thick tubular dendrites, subtracting somas before deploying ultra-fast chunked, multi-threaded `skimage` topological skeletonization across CPU cores.
3. **`core/barcode_detection.py` (Barcode Detection)**: Thresholds the secondary channels (e.g. 555nm and 640nm) to locate fluorescent barcodes and structurally filters them (e.g., discards barcodes outside the neurite mask or inside the soma mask).
4. **`core/graph_export.py` (Graph Exporting)**: Merges the datasets! Exports the `488` Somas as isolated centroids and Neurite Skeletons directly into unified JSON (CW-Complex) and SWC formats, scaled to absolute physical coordinates.
5. **`visualization/proofreader.py` (Interactive Proofreader)**: A lightweight Napari interface tailored for reviewing raw images, neurite/soma masks, skeletons, and filtered/discarded barcodes in 3D.

## Getting Started

You can supply the 488 target TIFF file and optional barcode TIFF files (555, 640).

### Run the Pipeline
For Windows:
```powershell
.\run_pipeline.bat --input_file "path/to/488.tif" --input_file_555 "path/to/555_barcode.tif" --output_dir "pipeline_output" --visualize
```

For Linux / Mac:
```bash
./run_pipeline.sh --input_file "path/to/488.tif" --input_file_555 "path/to/555_barcode.tif" --output_dir "pipeline_output" --visualize
```
*(Alternatively, execute `python main.py` directly with the same arguments).*

### Advanced Overrides
- **Multi-Channel**: 
  - `--input_file_555 <path>` (Loads first barcode channel)
  - `--input_file_640 <path>` (Loads second barcode channel)
- **Custom Thresholds**:
  - `--thresh_488 1200.5` (Tunes the strictness of the neurite extraction)
- **Physical Scaling**: Override the hardcoded voxel resolution for the JSON/SWC graph exports:
  - `--scale_x 0.1102 --scale_y 0.1102 --scale_z 0.5`
- **Output Naming**: If you don't want the pipeline to inherit the native filename prefix:
  - `--out_prefix "Sample_A"`
- **Hardware Fallback**: Append `--disable_gpu` to fall back entirely to CPU computation.

## Output Specifications

The pipeline creates an output directory populated with:

1. **Boolean Numpy Masks (`.npy`)**:
   - `[prefix]_soma_mask_488.npy`: 3D boolean volume of the cell bodies.
   - `[prefix]_neurite_mask_488.npy`: 3D boolean volume of the dendrites.
   - `[prefix]_skeleton_mask_488.npy`: 3D boolean volume of the 1-pixel wide morphological skeleton paths.
   - `[prefix]_filtered_barcodes_555.npy` and `640.npy`: Barcodes that successfully mapped to neurites.
   - `[prefix]_discarded_*.npy`: Structures and barcodes discarded during the topological filtering.
2. **SWC Files (`.swc`)**:
   - `[prefix]_skeletons.swc`: Raw voxel-coordinate topological graph.
   - `[prefix]_skeletons_micrometers.swc`: Physical graph scaled by the XYZ resolution parameters.
3. **CW-Complex JSON (`.json`)**:
   - `[prefix]_cw_complex.json`: Raw voxel-coordinate graph structured with vertices and edges.
   - `[prefix]_cw_complex_micrometers.json`: Physically scaled JSON graph.

## Visualization

The pipeline provides two powerful visualization tools built on Napari.

### 1. The Flexible Visualizer
If you want to view arbitrary sets of files, you can use the standalone `flex_visualizer.py`. It supports **any number of layers** simultaneously, as long as they use the known supported file extensions:
```bash
python visualization/flex_visualizer.py raw_image.tif soma_mask.npy neurite_mask.npy skeletons.swc skeletons.json another_mask.npy
```

### 2. The Interactive Proofreader
If you utilize the `--visualize` flag when running the pipeline, it will automatically launch the Interactive Proofreader immediately after generation, loading all filtered data and masks simultaneously. 

#### Hotkeys
- **Snap to Intensity (F)**: Select any skeleton shape with the Napari Vertex tool and press `F`. The script will search the local 3D neighborhood of the raw image and automatically snap every vertex of your selected skeleton precisely to the maximum fluorescent intensity peak!
- **Save Edits (S)**: Press `S` to instantly overwrite the `cw_complex.json` file with your modified graphs.
