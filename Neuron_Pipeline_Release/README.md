# 3D Neuron Skeletonization Pipeline

This package contains everything needed to extract ultra-clean, faint dendritic trees from 3D volume imaging using GPU-accelerated Frangi filtering and aggressive structural graph tracing.

## Usage

Run the `extract_skeletons.py` wrapper script to automatically process a volume and output perfectly formatted `.swc` files.

```bash
python extract_skeletons.py -i <path_to_3d_volume.tif> -o <path_to_output.swc>
```

### Outputs
- `_soma_labels.tif`: A mask of detected somas
- `output.swc`: Skeleton graph in pixel coordinates (for visualization overlays)
- `output_microns.swc`: Skeleton graph physically scaled to micron units

*(Optional: Add `--keep_intermediates` if you want to inspect the raw Frangi mask and raw Medial Axis Transform output)*

## Requirements
See `requirements.txt`. Requires an NVIDIA GPU for CuPy acceleration.
