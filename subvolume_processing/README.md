# 3D Subvolume & Whole Volume Processing Toolkit

This folder contains a collection of scripts for extracting, processing, visualizing, and analyzing 3D cell subvolumes and whole volumes, focusing on separating cell body somas and neurites (axons and dendrites) using structural filters.

---

## 📂 File Structure & Toolkit Overview

### 1. Subvolume Extraction & Search Scripts
- **[extract_soma_neurite_ch03.py](file:///c:/Users/banerjee/Desktop/um1_3d_volume/subvolume_processing/extract_soma_neurite_ch03.py)**: 
  - Downsamples the massive 3D volume, computes structural variance (neurites) and Gaussian-blurred Maximum Intensity Projection maps (somas) to locate optimal regions of interest containing high densities of both cell bodies and neurites.
  - Crops and exports the target region.
- **[extract_optimal_subvolume.py](file:///c:/Users/banerjee/Desktop/um1_3d_volume/subvolume_processing/extract_optimal_subvolume.py)**: 
  - Computes localized intensity metrics to programmatically find and crop out the absolute highest density cell clusters in 3D.
- **[manual_extract_subvolume.py](file:///c:/Users/banerjee/Desktop/um1_3d_volume/subvolume_processing/manual_extract_subvolume.py)**: 
  - Allows manual coordinates extraction of customized 3D bounding box regions of interest (ROIs).
- **[extract_ch04_matched.py](file:///c:/Users/banerjee/Desktop/um1_3d_volume/subvolume_processing/extract_ch04_matched.py)**: 
  - Extracts matching subvolume crops from Channel 04 (e.g. DAPI) at coordinates corresponding to selected regions in Channel 03 (FP).
- **[extract_subvolume.py](file:///c:/Users/banerjee/Desktop/um1_3d_volume/subvolume_processing/extract_subvolume.py)**: 
  - General utility script for quick, straightforward subvolume extraction.

### 2. Processing & Analysis Scripts
- **[neuron_processor.py](file:///c:/Users/banerjee/Desktop/um1_3d_volume/subvolume_processing/neuron_processor.py)**: 
  - Core subvolume processing algorithm.
  - Detects **somas** using Gaussian smoothing ($\sigma=5$), intensity percentile thresholding ($99.5\%$), binary hole-filling, and a minimum area size filter ($500$ voxels).
  - Detects **neurites** (dendrites/axons) using a multi-scale 3D Frangi vesselness filter (sigmas `[8, 12, 15, 20]`), thresholding, morphological closing, and dilation.
- **[process_whole_ch03_volume.py](file:///c:/Users/banerjee/Desktop/um1_3d_volume/subvolume_processing/process_whole_ch03_volume.py)**: 
  - Tiled, memory-mapped, and GPU-accelerated whole-volume processor for massive datasets (e.g., `271 x 2720 x 2720` voxels, ~8 GB).
  - Splits the volume into `(64, 512, 512)` tiles with boundary padding, runs the detection algorithm (leveraging GPU CuPy where possible), re-assembles the tiles, saves the final segmentations, and launches a unified Napari overlay.

### 3. Visualization Scripts
- **[visualize_subvolumes.py](file:///c:/Users/banerjee/Desktop/um1_3d_volume/subvolume_processing/visualize_subvolumes.py)**: 
  - Launches Napari displaying a single selected subvolume crop (rendered in magenta).

---

## 🏃 Quick Start Guide

Ensure you have your environment set up and package dependencies installed.

### 1. View a Subvolume
To quickly visualize a subvolume crop in Napari:
```bash
python visualize_subvolumes.py
```

### 2. Process a Subvolume (Detect Somas & Neurites)
To detect and visualize somas (in cyan) and neurites (in green) inside a subvolume:
```bash
python neuron_processor.py --input soma_neurite_subvolume_ch03.tif
```

### 3. Process the Entire Whole Volume (Tiled / GPU-Accelerated)
To process the entire `F0200_multichannel_cmle_ch03.tif` volume:
```bash
python process_whole_ch03_volume.py --workers 4
```
- `--workers`: Adjusts the number of parallel CPU process threads used.
- `--no-vis`: Skips launching Napari after processing.
- `--tile-size`: Customize tile dimensions (default: `64,512,512`).
