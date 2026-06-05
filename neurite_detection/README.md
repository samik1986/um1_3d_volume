# Neurite Detection & Topological CW Complex Pipeline

This repository contains a high-speed, memory-optimized, GPU-accelerated pipeline for extracting neurite networks from massive 3D microscopy TIFF volumes. The pipeline reconstructs the biology into a strict mathematical [CW Complex](https://en.wikipedia.org/wiki/CW_complex) topological graph format, explicitly modeling somas (cell bodies) and their attached neurites.

It includes **One-Click Execution** scripts, automatic **Batch Folder Processing**, and an interactive Napari GUI for **Topological Proofreading**.

---

## 🌟 Key Features

- **Massive Volume Processing**: Handles multi-gigabyte 3D TIFFs (e.g. 2720x2720x180) by splitting them into overlapping 3D memory chunks.
- **Extreme Performance**:
  - Fully GPU-accelerated (CuPy) Frangi vesselness and morphological filtering.
  - Sub-volume **Bounding Box Cropping** and optimized C++ Lee skeletonization to bypass CPU bottlenecks, reducing graph extraction times by over 80%.
- **Topological Strictness**: 
  - Carves out soma volumes so neurites perfectly terminate at the cell membrane.
  - Automatically maps sub-graphs to their parent somas (coloring them identically in the viewer).
- **Batch Processing**: Feed it a folder, and it will iteratively process every TIFF, generating distinct isolated output sub-directories.
- **Interactive Proofreading**: A custom Napari GUI with mathematical **Edge Snapping** to seamlessly edit and save the network.

---

## 📁 Core Functionalities & Modules

### 1. `process_neurites.py` (Neurite Masking)
High-speed GPU-accelerated Frangi vesselness filter featuring **Hysteresis Thresholding**. It splits massive 3D TIFFs into overlapping memory chunks, performs the neurite enhancement, propagates dim signals topologically via hysteresis, and applies morphological closing entirely on the GPU via CuPy. 

### 2. `detect_somas.py` (Cell Body Detection)
GPU-accelerated soma boundary detection. It processes the full volume in 3D chunks, filters for thick cell bodies using high-frequency smoothing and background subtraction, and assigns unique integer IDs to each detected soma via CPU connected-components.

### 3. `cw_extraction.py` (Topological Graph Generation)
Converts the 3D binary mask into an explicit 1D topological graph representation (`cw_complex.json`).
*   **Performance Crop**: Calculates the minimal 3D bounding box of all structures to strictly limit the CPU skeletonization workload to dense areas.
*   **Soma Carving**: Subtracts detected soma volumes from the neurite mask to guarantee neurites terminate exactly at the cell walls.
*   **Topology Mapping**: Connected neurite sub-graphs are traced and mapped to their adjoining somas. Unconnected structures are tracked as orphans.
*   **CW Complex Generation**: Records graph nodes (0-cells), paths (1-cells), tube surfaces and soma bounding boxes (2-cells), and voxel volumes (3-cells) into a complete JSON specification.

### 4. `run_pipeline.py` (Master Orchestrator)
The overarching control script that manages the sequential execution of the pipeline. It seamlessly handles both **Single Files** and **Batch Folders**, automatically generating conflict-free output directories.

### 5. `utils/viewer.py` (Interactive Proofreading)
A specialized Napari-based proofreading tool that loads the original raw image alongside the extracted topological graph and 3D soma labels. It features **Automatic Structural Coloring**, where neurite edges are dynamically colored to match their corresponding parent soma cell body for intuitive review.

---

## 🚀 Execution Guide

### Option 1: One-Click Execution (Machine Independent)
The easiest way to run the pipeline is to use the provided bash/batch scripts. These scripts automatically create an isolated Python virtual environment, install all dependencies from `requirements.txt`, and launch the pipeline.

**For Windows:**
Simply drag and drop your `.tif` file OR a folder containing multiple `.tif` files onto `run_windows.bat` in the file explorer.
Alternatively, via command line:
```cmd
run_windows.bat path\to\your\image.tif
# OR
run_windows.bat path\to\your\folder_of_tiffs
```

**For Linux/macOS:**
```bash
./run_linux.sh path/to/your/image.tif
# OR
./run_linux.sh path/to/your/folder_of_tiffs
```

*Note: If a folder is provided, the script will automatically batch process all TIFF files inside it, creating a separate output subdirectory for each file, and it will suppress the Napari viewer from opening automatically to prevent blocking the pipeline queue.*

### Option 2: Automated Pipeline (Manual Python)
If you already have your environment setup, you can run the master script directly:

```bash
cd neurite_detection
python run_pipeline.py --input "path/to/your/image.tif" --outdir "output"
```

### Option 3: Standalone Execution
If you wish to run the modules individually (e.g. for testing parameters or running on a headless server), follow these steps in order:

1. **Process Neurites**
```bash
python process_neurites.py --input "path/to/image.tif" --output "output/neurite_mask.tif"
```

2. **Detect Somas**
```bash
python detect_somas.py --input "path/to/image.tif" --output "output/soma_labels.tif"
```

3. **Extract Topology (CW Complex)**
```bash
python cw_extraction.py --input "output/neurite_mask.tif" --output "output/cw_complex.json" --somas "output/soma_labels.tif"
```

4. **Open the Proofreading Viewer**
```bash
python utils/viewer.py --raw "path/to/image.tif" --cw "output/cw_complex.json" --mask "output/neurite_mask.tif" --somas "output/soma_labels.tif"
```

---

## 🛠️ Proofreading Keybindings

When using the interactive proofreading viewer (`utils/viewer.py`):
- In Napari, select the `0-Cells (Nodes)` layer to add/move/delete junctions and endpoints.
- Select the `1-Cells (Edges)` layer to modify the paths.
- **Geometric Edge Snapping**: Newly added or edited edges will mathematically snap their `[Z, Y, X]` coordinates to the nearest neurite centerline, guaranteeing physical and topological continuity is maintained in the final graph.
- Press **`S`** to overwrite and save your topological edits directly back into the `cw_complex.json` file on disk.

---

## ⚙️ System Requirements
- Python 3.9+
- `cupy-cuda12x` (Required for GPU acceleration. Adjust `12x` based on your CUDA version)
- `sknw` (for graph extraction)
- `scikit-image >= 0.19.0` (for fast Lee skeletonization)
- `napari[all]`
