# Centroid CW-Complex Processing

This module is responsible for parsing raw cell centroid locations (stored as a collection of slice-wise SWC files) and converting them into a standardized 1D CW-Complex JSON format.

## Overview

A CW-Complex is a mathematical construct used to represent networks. In this format:
- `0-cells` represent the nodes (in this case, isolated points or cell centroids).
- `1-cells` represent the edges connecting nodes (which are intentionally left empty for raw centroid sets, as they do not possess a topological skeleton).

This allows downstream analysis scripts to treat cell centroids with the same universal format used for fully connected neuronal networks.

## Structure

- `process_centroids.py`: The main Command Line Interface (CLI) application.
- `utils.py`: Contains the logic for SWC parsing (`parse_swc_files`) and JSON generation (`serialize_to_cw_complex`).

## Usage

You can run the script directly from the command line by specifying the input directory containing the SWC files and the output destination for the compiled JSON.

```bash
python process_centroids.py --input "C:\path\to\swc\slices" --output "C:\path\to\output\centroid_cw_complex.json"
```

### Arguments

*   `-i`, `--input`: **(Required)** The directory containing `.swc` files (e.g., `A3_ch04_slice0001.swc`).
*   `-o`, `--output`: **(Required)** The full filepath where the resulting `.json` file should be written.

### Example

```bash
cd centroid_cw_processing
python process_centroids.py -i "..\a3_ch04_Swc\slices" -o "centroid_cw_complex.json"
```

## Data Output Format

The output JSON contains the following structure:
*   `metadata`: Describes each key within the document.
*   `network_type`: Identifies the graph structure type (e.g., `"1D CW Complex Forest"`).
*   `cells_0_nodes`: A list of the cell centroids containing unique IDs, their classification type (`"boundary"`), and their 3D coordinates `[Z, Y, X]`. All spatial coordinates are strict integers.
*   `cells_1_linestrings`: An empty list.
