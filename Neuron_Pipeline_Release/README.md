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

*(Optional: Add `--res_x`, `--res_y`, and `--res_z` to specify the physical pixel resolution in microns. Defaults are X: 0.1102, Y: 0.1102, Z: 0.5)*

## Examples

### 1. Standard Extraction
Extract neurons from a volume and save the SWC file (and its micron-scaled duplicate) into an output folder. Intermediate mask files are automatically cleaned up.
```bash
python extract_skeletons.py -i "..\data_046\F0046_multichannel_cmle_ch03.tif" -o "..\output\my_neurons.swc"
```

### 2. Extraction for Debugging (Keep Intermediates)
If you want to view the raw Frangi filter output or the raw Medial Axis Transform skeleton, pass the `--keep_intermediates` flag.
```bash
python extract_skeletons.py -i "..\data_046\F0046_multichannel_cmle_ch03.tif" -o "..\output\my_neurons.swc" --keep_intermediates
```

### 3. Extraction with Custom Physical Resolution
If your imaging setup uses a different voxel size, you can override the defaults (X: 0.1102, Y: 0.1102, Z: 0.5) by specifying the XYZ resolution in microns/pixel.
```bash
python extract_skeletons.py -i "..\data_046\F0046_multichannel_cmle_ch03.tif" -o "..\output\my_neurons.swc" --res_x 0.3 --res_y 0.3 --res_z 1.0
```

### 4. Visualizing the Result
Once the extraction completes, you can view the pixel-aligned `.swc` over your raw volume in Napari using the provided visualizer.
```bash
python visualize_skeletons.py --volume "..\data_046\F0046_multichannel_cmle_ch03.tif" --swc "..\output\my_neurons.swc"
```

### 5. Batch Processing via CSV
If you have multiple volumes to process, create a `.csv` file with two headers: `input` and `output`.

**example_batch.csv**:
```csv
input,output
..\data\volume1.tif,..\output\vol1.swc
..\data\volume2.tif,..\output\vol2.swc
```

Then run the batch processor (you can also pass `--res_x`, `--res_y`, `--res_z` here!):
```bash
python batch_process.py example_batch.csv
```

## Requirements
See `requirements.txt`. Requires an NVIDIA GPU for CuPy acceleration.
