# Single-Channel Neurite & Soma Extraction Pipeline

A highly optimized, GPU-accelerated pipeline built to extract massively scaled 3D Somas and Neurite Skeletons strictly from a single massive `488` image volume. 

The pipeline handles dense, noisy volumes by automatically slicing the array into parallel chunks, filtering high/low frequency artifacts on the GPU with CuPy, calculating the Somas, and explicitly subtracting them to generate pristine skeletonizations with multi-threaded CPU evaluation.

## Architecture & Logic

1. **`core/cell_detection.py` (Soma Extraction)**: Isolates 3D somas across massive volumes. It utilizes Gaussian high/low frequency smoothing and percentile-based filtering on CuPy arrays to locate dense soma clusters. It explicitly uses **heavy morphological opening (erosions + dilations)** to completely sever any thick tubular dendrites attached to the somas, leaving perfectly isolated cell bodies.
2. **`core/neurite_detection.py` (Skeletonization)**: Uses a highly parallelized **Analytical 3D Frangi Vesselness** filter on CuPy with a safe `gpu_semaphore=1` constraint to avoid PCIe thrashing. It is specially tuned to extract **thick, bright tubular dendrites** (`sigmas=[2.0, 4.0]`, `thresh=0.05`) while aggressively ignoring thin, faint noise and small disconnected fragments. The somas are carefully subtracted from this mask post-Frangi filtering, before deploying an ultra-fast **chunked, multi-threaded `skimage` topological skeletonization** across 8 CPU cores.
3. **`core/graph_export.py` (Graph Exporting)**: Merges the datasets! It exports the `488` Somas as explicit isolated centroids (Node Type `2`) and the Neurite Skeletons (Node Type `3`) directly into unified JSON (CW-Complex) and SWC formats, scaled to absolute physical coordinates.
4. **`visualization/proofreader.py` (Interactive Proofreading)**: A lightweight Napari interface tailored for editing massive datasets. Features intensity snapping and real-time disk saving.

## Getting Started

You only need to supply your target TIFF file. The script will automatically derive a prefix from your filename and prepend it to all outputs in your designated folder.

### Run the Pipeline
```powershell
python main.py --input_file "path/to/your/488_channel.tif" --output_dir "pipeline_output" --visualize
```

### Advanced Overrides
- **Custom Thresholds**: You can manually override the Otsu cutoff thresholds for either step:
  - `--thresh_488 1200.5` (Tunes the strictness of the neurite extraction)
  - `--thresh_488_soma 95.0` (Tunes the percentile cutoff for the soma extraction)
- **Output Naming**: If you don't want the pipeline to inherit the native filename prefix:
  - `--out_prefix "Sample_A"`
- **Hardware Fallback**: If your VRAM is completely overwhelmed, append `--disable_gpu` to fall back entirely to CPU computation.

## Proofreading Edits

If you utilize the `--visualize` flag, the pipeline will launch Napari immediately after generating the files, loading the massive original array via lazy memory-mapping (`tifffile.memmap`), alongside the extracted Somas and Skeletons.

### Hotkeys
- **Snap to Intensity (F)**: Select any skeleton shape with the Napari Vertex tool and press `F`. The script will search the local 3D neighborhood of the raw image and automatically snap every vertex of your selected skeleton precisely to the maximum fluorescent intensity peak!
- **Save Edits (S)**: Press `S` to instantly overwrite the `cw_complex.json` file with your modified graphs.
