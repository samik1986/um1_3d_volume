# Algorithmic Overview: 3D Neuron Skeletonization Pipeline

**Author:** Samik Banerjee  
**Last updated on:** August 28, 2026  

This pipeline is designed to extract incredibly faint dendritic structures from noisy 3D volumes. It achieves this by combining extreme-sensitivity physical filters with aggressive, graph-level topological pruning.

Here is a breakdown of the four core steps:

## 1. Soma Detection (`detect_somas.py`)
- **Objective:** Identify the large, bright cell bodies (somas) to prevent them from dominating and interfering with the thin-vessel detection algorithm.
- **Method:** 
  - Applies a Gaussian blur to smooth the image.
  - Thresholds the volume (default `0.3` for `ch03`) and filters out small, spurious bright spots based on volume constraints (`>200` voxels).
  - Performs 3D connected-components labeling.
  - Expands the detected somas slightly (binary dilation) to ensure the entire cell body structure is safely masked out before neurite processing.

## 2. Neurite Detection (`process_neurites.py`)
- **Objective:** Highlight thin, string-like structures (dendrites/axons) while mathematically suppressing isotropic noise and flat planar artifacts.
- **Method:**
  - Uses a **GPU-accelerated 3D Frangi Vesselness Filter**.
  - Computes the 3D Hessian matrix using Gaussian second derivatives (at a specific `sigma=1.5` to smooth over noisy surface bumps).
  - Evaluates the three eigenvalues to determine if a local voxel structure is geometrically tubular.
  - **Key Innovation:** Operates with an extremely low, absolute normalization constant (`c=5e-4`) instead of computing dynamic per-tile maximums. This prevents severe "noise amplification" in dark regions and allows us to pull out ultra-faint neurites using a highly sensitive absolute threshold (`0.02`).

## 3. Fast Skeletonization (`skeletonize_fast.py`)
- **Objective:** Reduce the thick, tubular 3D Frangi masks down to 1-pixel-wide topological centerlines.
- **Method:**
  - Uses a 3D Medial Axis Transform (MAT) algorithm based on Lee's topological thinning.
  - Operates chunk-by-chunk using a multiprocessed worker pool (`--workers`) to vastly accelerate the heavy morphological operations across massive volumes.

## 4. Graph Tracing & Pruning (`trace_and_connect_skeletons.py`)
- **Objective:** Convert the 1-pixel-wide skeleton voxel mask into a vector-based mathematical graph (`.swc`), while physically destroying noise artifacts ("spiderwebs" or "tumbleweeds") caused by the extreme sensitivity of Step 2.
- **Method:**
  - Converts the skeleton mask into a `NetworkX` spatial graph using KD-Trees to aggressively connect neighboring voxels.
  - Analyzes the topological degree of every node: Nodes with 1 connection are *endpoints*; nodes with >2 are *branch points*.
  - **Graph-Level Pruning (The "String-Like" Logic):**
    - Identifies all paths between branch points ("backbones"). If a backbone is shorter than **15 pixels**, it is shattered (deleted). This completely destroys the dense, recursive "spiderweb" loop meshes that form on the surface of noisy dendrites.
    - Identifies all paths from branch points to endpoints ("twigs"). If a twig is shorter than **80 pixels**, it is considered a false surface branch and deleted.
    - Identifies completely isolated lines (no branches). If an isolated line is shorter than **150 pixels**, it is considered background speckle noise and deleted.
  - Finally, it downsamples the remaining long, pristine strings (e.g., takes every 10th point) and physically scales the geometry by the provided XYZ resolution (`--res_x`, `--res_y`, `--res_z`). The result is saved to standard `.swc` formats.

## 5. Topological Validation (`validate_neuron_swc.py`)
- **Objective:** Mathematically verify that the generated SWC output actually represents valid biological dendritic geometry, rather than noise or meshes.
- **Method:**
  - Evaluates standard 7-column SWC syntax correctness.
  - Reconstructs the physical graph and mathematically checks for **cycles (loops)**. Real dendritic trees have no loops; if loops exist, the geometry is physically flawed (spiderweb noise).
  - Calculates physical Euclidean span lengths of all continuous fragments.
  - Groups fragments into biological **"Neurons"** (length >= 100 units) and **"Small Fragments"** (length < 100 units, likely noise speckles).
  - Evaluates topological degree to detect the presence of biological branch points and endpoints.
  - Automatically fails/warns if the tree is overly shattered or contains non-biological loops, confirming whether the pipeline's pruning steps were successful.
