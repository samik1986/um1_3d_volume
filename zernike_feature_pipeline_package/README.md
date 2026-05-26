# Zernike 3D Batch Feature Extraction Pipeline Package

> **Created by: Samik Banerjee @ Mitralab @ Cold Spring Harbor Laboratory (CSHL)**

This standalone package provides a GPU-accelerated 3D shape descriptor extraction pipeline for cell somas. It maps coordinate lists from physical microns space, compiles a Zernike filter bank in parallel on GPU, extracts morphological descriptors, and computes similarity pairings in real-time.

---

## 📦 Package Structure

- **`batch_process_zernike.py`**: Entry script. Resolves paths relatively, loads datasets, runs extraction, and computes nearest-neighbor twins.
- **`build_zernike_filter_gpu.py`**: GPU filter bank compiler. Leverages CuPy to compile hundreds of Zernike basis functions in parallel.
- **`zernike_basis_gpu.py`**: Low-level CUDA/GPU mathematical implementations of radial and spherical Zernike harmonics.
- **`data/`**: Subfolder containing packaged input data:
  - `centroids_DAPI_scaled.swc`: Packaged physical DAPI centroid coordinates (633 cells).
  - `optimal_basis_keys.json`: 408 custom optimal filter keys representing 54 energy shells.
  - `zernike_features_dapi.csv`: Generated output shell invariants.
  - `nearest_neighbors.csv`: Generated morphological similarity twin-mapping file.

---

## 🏃 Running the Pipeline

Ensure you have a Python environment with CUDA-compatible `cupy`, `tifffile`, `pandas`, and `numpy` installed.

Run the batch extraction directly:
```bash
python batch_process_zernike.py
```

### Output Results
- Detailed logs will display parallel GPU filter bank compilation and fast descriptor extraction metrics.
- Output features and neighboring pairs will be written directly inside the `data/` subdirectory.
