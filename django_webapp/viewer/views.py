"""
views.py (django_webapp viewer)

Author: Samik Banerjee
Date: May 8, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

Django views for the biological viewer application. 
Handles volume loading, downsampling, and SWC parsing.
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import tifffile
import pandas as pd
import numpy as np
import io
import math

# Global state to hold volume and data
volume_data = {
    'tif': None,
    'pages': None,
    'shape': None,
    'num_slices': 0,
    'centroids': pd.DataFrame(columns=['id', 'type', 'x', 'y', 'z', 'r', 'p']),
    'downsampled': None # We will pre-downsample it upon load so dash_apps can pick it up instantly
}

def parse_swc(filepath):
    try:
        # Standard SWC reading
        df = pd.read_csv(filepath, sep=' ', comment='#', header=None, 
                         names=['id', 'type', 'x', 'y', 'z', 'r', 'p'], skipinitialspace=True)
        # Drop rows with NaN
        df = df.dropna()
        return df
    except Exception as e:
        print(f"Error reading SWC: {e}")
        return pd.DataFrame(columns=['id', 'type', 'x', 'y', 'z', 'r', 'p'])

def index(request):
    is_loaded = volume_data.get('downsampled') is not None
    return render(request, 'viewer/index.html', {'is_loaded': is_loaded})

@csrf_exempt
def load_volume(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        tiff_path = data.get('tiff_path')
        swc_path = data.get('swc_path')
        
        try:
            if tiff_path:
                volume_data['tif'] = tifffile.TiffFile(tiff_path)
                volume_data['pages'] = volume_data['tif'].pages
                volume_data['num_slices'] = len(volume_data['pages'])
                volume_data['shape'] = volume_data['pages'][0].shape
                
                # Pre-downsample for Dash-VTK
                num_slices = volume_data['num_slices']
                h, w = volume_data['shape']
                
                z_step = max(1, num_slices // 64)
                xy_step = max(1, w // 128)
                
                slices = list(range(0, num_slices, z_step))
                z_dim = len(slices)
                
                out_h = int(math.ceil(h / xy_step))
                out_w = int(math.ceil(w / xy_step))
                
                downsampled = np.zeros((z_dim, out_h, out_w), dtype=np.float32)
                
                for i, z in enumerate(slices):
                    img_arr = volume_data['pages'][z].asarray().astype(np.float32)
                    sub_arr = img_arr[::xy_step, ::xy_step]
                    sh, sw = sub_arr.shape
                    downsampled[i, :sh, :sw] = sub_arr
                    
                p2, p98 = np.percentile(downsampled, (2, 98))
                downsampled = np.clip((downsampled - p2) / (p98 - p2 + 1e-5), 0, 1)
                downsampled = (downsampled * 255).astype(np.uint8)
                
                volume_data['downsampled'] = downsampled
                volume_data['steps'] = (z_step, xy_step)

            if swc_path:
                volume_data['centroids'] = parse_swc(swc_path)
                
            return JsonResponse({
                'status': 'success',
                'meta': {
                    'shape': volume_data['shape'] if volume_data['shape'] else [],
                    'slices': volume_data['num_slices']
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'invalid method'}, status=405)
