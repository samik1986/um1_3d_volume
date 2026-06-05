# Neurite Detection Pipeline

This directory contains a fast, memory-optimized, GPU-accelerated pipeline for extracting neurites from 3D microscopy volumes and converting them into a topological CW Complex graph format. It also includes an interactive Napari viewer for proofreading the extracted structures.

## System Requirements
- Python 3.9+
- `cupy` (for GPU acceleration)
- `sknw` (for graph extraction)
- `scikit-image`
- `napari`

## Folder Structure Walkthrough

*   **`process_neurites.py`**: High-speed GPU-accelerated Frangi vesselness filter with **Hysteresis Thresholding**. It splits massive 3D TIFFs into overlapping memory chunks, performs the neurite enhancement, hysteresis propagation, and morphological closing entirely on the GPU via CuPy, and reconstructs the boolean mask.
*   **`detect_somas.py`**: GPU-accelerated soma boundary detection. It processes the full volume in 3D chunks, filters for thick cell bodies, and assigns unique integer IDs to each detected soma.
*   **`cw_extraction.py`**: Converts the 3D binary mask into an explicit 1D topological graph representation.
    *   **Soma Carving**: It subtracts detected soma volumes from the neurite mask to guarantee neurites terminate exactly at the cell body walls.
    *   **Topology Mapping**: Connected neurite sub-graphs are topologically traced and mapped to their adjoining somas. Unconnected structures are tracked as orphans.
    *   **CW Complex Generation**: It records graph nodes (0-cells), paths (1-cells), tube surfaces and soma bounding boxes (2-cells), and voxel volumes (3-cells) into a complete JSON specification.
*   **`run_pipeline.py`**: The master orchestration script that executes the above modules sequentially.
*   **`CW_COMPLEX_SPEC.md`**: Formal specification document describing the JSON architecture of the topological output.
*   **`utils/`**: Subfolder containing utility tools for topological editing and proofreading.
    *   **`utils/viewer.py`**: A specialized Napari-based proofreading tool that loads the original raw image alongside the extracted topological graph and 3D soma labels. It features **Automatic Structural Coloring**, where neurite components are dynamically colored to match their corresponding parent soma cell body for intuitive review.

---

## 🚀 Execution Guide

### Option 1: One-Click Execution (Machine Independent)
The easiest way to run the pipeline is to use the provided execution scripts. These scripts automatically create an isolated Python virtual environment, install all dependencies from `requirements.txt`, and launch the pipeline.

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

*Note: If a folder is provided, the script will automatically batch process all TIFF files inside it, creating a separate output subdirectory for each file, and it will suppress the Napari viewer from opening automatically to prevent blocking the pipeline.*

### Option 2: Automated Pipeline (Manual Python)
If you already have your environment setup, you can run the master script directly:

```bash
cd neurite_detection
python run_pipeline.py --input "path/to/your/image.tif" --outdir "output"
```

The script will automatically:
1. Detect neurites on the GPU.
2. Detect 3D somas on the GPU.
3. Carve somas, extract the skeleton, map component topologies, and build `cw_complex.json`.
4. Launch the Napari proofreading viewer.

*(Note: Pass `--no-vis` to skip the automatic visualizer launch)*

### Option 2: Standalone Execution
If you wish to run the modules individually (e.g. for testing parameters or running on a headless server), follow these steps in order:

**1. Process Neurites**
```bash
python process_neurites.py --input "path/to/image.tif" --output "output/neurite_mask.tif"
```

**2. Detect Somas**
```bash
python detect_somas.py --input "path/to/image.tif" --output "output/soma_labels.tif"
```

**3. Extract Topology (CW Complex)**
```bash
python cw_extraction.py --input "output/neurite_mask.tif" --output "output/cw_complex.json" --somas "output/soma_labels.tif"
```

**4. Open the Proofreading Viewer**
```bash
python utils/viewer.py --raw "path/to/image.tif" --cw "output/cw_complex.json" --mask "output/neurite_mask.tif" --somas "output/soma_labels.tif"
```

---

## Proofreading Keybindings
When using the proofreading viewer (`utils/viewer.py`):
- In Napari, select the `0-Cells (Nodes)` layer to add/move/delete junctions and endpoints.
- Select the `1-Cells (Edges)` layer to modify the paths.
- **Edge Snapping**: Newly added or edited edges automatically snap to the nearest neurite centerlines, ensuring physical and topological continuity is maintained.
- Press **`S`** to overwrite and save your topological edits directly back into the `cw_complex.json` file on disk.
