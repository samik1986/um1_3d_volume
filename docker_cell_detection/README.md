# 3D Cell Detection and Validation Pipeline

This pipeline provides a robust, memory-efficient solution for detecting 3D cell centroids across multiple biological channels (DAPI and FP) and performing spatial cross-validation.

## Features

-   **Parallel Processing**: High-speed detection using multiple CPU cores via `ProcessPoolExecutor`.
-   **Memory Efficient**: Processes large 3D TIFF volumes in overlapping blocks (tiling) to avoid Out-Of-Memory (OOM) errors.
-   **Dual-Channel Validation**: Detects centroids in both DAPI and FP channels. Validates FP detections by ensuring a DAPI centroid exists within a specified spatial proximity.
-   **Automatic Scaling**: Converts voxel-space coordinates (pixels) into physical units using provided resolution factors.
-   **Caching**: Automatically reuses existing `.swc` detection files to skip redundant processing if the files already exist.
-   **Containerized**: Fully compatible with Docker for reproducible execution.

## Installation

### Local Setup
Ensure you have Python 3.11+ installed. Install the required dependencies:

```bash
pip install -r requirements.txt
```

### Docker Setup
Build the Docker image from the project root:

```bash
docker build -t cell-detection -f docker_cell_detection/Dockerfile .
```

## Usage

### 1. Running the Standard Pipeline (Sequential)
Best for machines with limited RAM. It caches results automatically.

```bash
python run_pipeline.py --dapi ch04.tif --fp ch03.tif --dist_thresh 120.0
```

### 2. Running the Parallel Pipeline (High Speed)
Leverages multiple CPU cores. Recommended for machines with 16GB+ RAM.

```bash
python run_pipeline_parallel.py --workers 4 --dist_thresh 120.0
```

### 3. Running via Docker
Mount your data directory to `/data` in the container:

```bash
docker run -v "C:/path/to/data:/data" cell-detection --dapi /data/ch04.tif --fp /data/ch03.tif
```

## Core Arguments

| Argument | Default | Description |
| :--- | :--- | :--- |
| `--dapi` | `F0200...ch04.tif` | Path to the DAPI channel volume. |
| `--fp` | `F0200...ch03.tif` | Path to the FP channel volume. |
| `--workers` | `4` | (Parallel only) Number of CPU cores to use. |
| `--dist_thresh` | `120.0` | Max distance (pixels) between FP and DAPI for validation. |
| `--force` | `False` | Force re-detection even if SWC files exist. |
| `--scale_x/y` | `0.1102` | Resolution in XY plane. |
| `--scale_z` | `0.5` | Resolution in Z axis. |

## Pipeline Workflow

1.  **Phase 1 (DAPI)**: Detects centroids in the DAPI channel. Outputs `centroids_DAPI.swc` and `centroids_DAPI_scaled.swc`.
2.  **Phase 2 (FP)**: Detects centroids in the FP channel (Area >= 40px). Outputs `centroids_FP.swc` and `centroids_FP_scaled.swc`.
3.  **Phase 3 (Validation)**: Filters FP centroids. An FP centroid is kept only if there is a DAPI centroid within the `dist_thresh`.
4.  **Phase 4 (Final Output)**: Saves the validated results to `centroids_FP_final.swc` and `centroids_FP_final_scaled.swc`.

## Visualization

You can visualize the results using **napari**:

```bash
python visualize_napari.py
```
*(Note: Ensure your TIFF files and SWCs are in the same folder or parent folder relative to the script.)*

---
*Developed for the um1_3d_volume project.*
