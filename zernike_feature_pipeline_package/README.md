# Zernike 3D Batch Feature Extraction Pipeline Package

> **Created by: Samik Banerjee @ Mitralab @ Cold Spring Harbor Laboratory (CSHL)**

This standalone package provides a GPU-accelerated 3D shape descriptor extraction pipeline for cell somas. It maps coordinate lists from physical microns space, compiles a Zernike filter bank in parallel on GPU, extracts morphological descriptors, and computes similarity pairings in real-time.

---

## 📦 Package Structure

- **`launcher.py`**: Self-contained dependency bootstrapper that auto-installs missing packages (`numpy`, `pandas`, `scipy`, `tifffile`, `cupy`) on execution.
- **`run_pipeline.bat`**: Double-click execution batch script for Windows. Safely detects missing Python environments and directs the user to the installation portal.
- **`run_pipeline.sh`**: Double-click execution shell script for macOS and Linux environments.
- **`data/`**: Subfolder containing packaged input data:
  - `centroids_DAPI_scaled.swc`: Packaged physical DAPI centroid coordinates (633 cells).
  - `optimal_basis_keys.json`: 408 custom optimal filter keys representing 54 energy shells.
  - `zernike_features_dapi.csv`: Generated output shell invariants.
  - `nearest_neighbors.csv`: Generated morphological similarity twin-mapping file.

---

## 🏃 Running the Pipeline

The pipeline is pre-configured with **one-click auto-installers** that dynamically verify your Python environment, boot-strap `pip`, and automatically install all needed CUDA-accelerated mathematical libraries before running extraction.

### Windows (Double-Click Execution)
Simply double-click the Windows batch runner:
```bash
run_pipeline.bat
```

### macOS / Linux (Terminal Launch)
Open a terminal in the folder directory and run:
```bash
./run_pipeline.sh
```

---

## ⚙️ Custom Modular Parameters

You can also pass custom inputs directly through the launchers or manual script execution:
```bash
python batch_process_zernike.py \
    --volume /path/to/custom_volume.tif \
    --centroids /path/to/custom_centroids.swc \
    --output_prefix custom_dapi
```

#### CLI Parameters:
- **`--volume`**: Path to custom 3D TIFF intensity volume (Defaults to `F0200_multichannel_cmle_ch04.tif`).
- **`--centroids`**: Path to custom SWC coordinates. Supports scaled physical dimensions in microns (Defaults to packaged `centroids_DAPI_scaled.swc`).
- **`--output_prefix`**: Output file prefix. Saves output tables dynamically to `data/{prefix}_features.csv` and `data/{prefix}_neighbors.csv` (Defaults to `zernike`).
