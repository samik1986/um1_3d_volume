"""
app.py (webapp)

Author: Samik Banerjee
Date: May 8, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

Flask-based web application for interactive 2D/3D visualization of 
large TIFF volumes and cell detection centroids.
"""

import os
import io
import json
import numpy as np
import pandas as pd
import tifffile
from PIL import Image
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024  # 10 GB limit for local large files
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global variables to store loaded data
volume_data = {
    'tif': None,
    'pages': None,
    'shape': None,
    'num_slices': 0,
    'centroids': pd.DataFrame(columns=['id', 'type', 'x', 'y', 'z', 'r', 'p'])
}

volume_progress = 0

def load_swc(filepath):
    try:
        # standard SWC
        df = pd.read_csv(filepath, sep=' ', comment='#', header=None, 
                         names=['id', 'type', 'x', 'y', 'z', 'r', 'p'])
        return df
    except Exception as e:
        print(f"Error reading SWC: {e}")
        return pd.DataFrame(columns=['id', 'type', 'x', 'y', 'z', 'r', 'p'])

def close_volume():
    if volume_data['tif'] is not None:
        volume_data['tif'].close()
        volume_data['tif'] = None
    volume_data['pages'] = None
    volume_data['shape'] = None
    volume_data['num_slices'] = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/load_local', methods=['POST'])
def load_local():
    data = request.json
    tiff_path = data.get('tiff_path', '')
    swc_path = data.get('swc_path', '')

    if not os.path.exists(tiff_path):
        return jsonify({'error': f'TIFF file not found: {tiff_path}'}), 404

    close_volume()

    try:
        # Open lazily to save RAM
        volume_data['tif'] = tifffile.TiffFile(tiff_path)
        volume_data['pages'] = volume_data['tif'].pages
        volume_data['num_slices'] = len(volume_data['pages'])
        h, w = volume_data['pages'][0].shape
        volume_data['shape'] = (w, h)
        
        if swc_path and os.path.exists(swc_path):
            volume_data['centroids'] = load_swc(swc_path)
        else:
            volume_data['centroids'] = pd.DataFrame(columns=['id', 'type', 'x', 'y', 'z', 'r', 'p'])

        return jsonify({
            'success': True,
            'num_slices': volume_data['num_slices'],
            'width': w,
            'height': h,
            'num_centroids': len(volume_data['centroids'])
        })
    except Exception as e:
        close_volume()
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_files():
    if 'tiff_file' not in request.files:
        return jsonify({'error': 'No TIFF file uploaded'}), 400
    
    tiff_file = request.files['tiff_file']
    swc_file = request.files.get('swc_file')
    
    if tiff_file.filename == '':
        return jsonify({'error': 'Empty TIFF filename'}), 400

    tiff_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(tiff_file.filename))
    tiff_file.save(tiff_path)
    
    swc_path = ''
    if swc_file and swc_file.filename != '':
        swc_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(swc_file.filename))
        swc_file.save(swc_path)
        
    # Redirect to the local load mechanism now that it's on disk
    with app.test_request_context('/api/load_local', method='POST', json={'tiff_path': tiff_path, 'swc_path': swc_path}):
        return load_local()

@app.route('/api/slice/<int:z>')
def get_slice(z):
    if volume_data['pages'] is None or z < 0 or z >= volume_data['num_slices']:
        return "Invalid slice", 404
        
    try:
        # Read just this slice
        img_arr = volume_data['pages'][z].asarray()
        
        # Normalize to 8-bit for PNG transmission
        if img_arr.dtype == np.uint16 or img_arr.dtype == np.float32:
            # Auto-contrast using 2nd and 98th percentiles
            p2, p98 = np.percentile(img_arr, (2, 98))
            img_arr = np.clip((img_arr - p2) / (p98 - p2 + 1e-5), 0, 1) * 255
            img_arr = img_arr.astype(np.uint8)
            
        img = Image.fromarray(img_arr)
        
        # Serve image
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/png')
    except Exception as e:
        return str(e), 500

@app.route('/api/points/<int:z>')
def get_points(z):
    df = volume_data['centroids']
    if df.empty:
        return jsonify([])
        
    # SWC points might not be perfectly integers. We grab points within +/- 1 z-slice.
    margin = 1.0
    slice_points = df[(df['z'] >= (z - margin)) & (df['z'] <= (z + margin))]
    
    points = [{'x': row['x'], 'y': row['y'], 'r': row['r']} for _, row in slice_points.iterrows()]
    return jsonify(points)

@app.route('/api/volume3d_progress')
def get_progress():
    global volume_progress
    return jsonify({'progress': volume_progress})

@app.route('/api/volume3d')
def get_volume3d():
    global volume_progress
    volume_progress = 0
    if volume_data['tif'] is None:
        return jsonify({'error': 'No volume loaded.'}), 400
        
    try:
        print("Downsampling volume for Three.js...")
        num_slices = volume_data['num_slices']
        h, w = volume_data['shape']
        
        z_step = max(1, num_slices // 64)
        xy_step = max(1, w // 128)
        
        slices = list(range(0, num_slices, z_step))
        z_dim = len(slices)
        
        out_h = int(np.ceil(h / xy_step))
        out_w = int(np.ceil(w / xy_step))
        
        downsampled = np.zeros((z_dim, out_h, out_w), dtype=np.float32)
        
        for i, z in enumerate(slices):
            img_arr = volume_data['pages'][z].asarray().astype(np.float32)
            sub_arr = img_arr[::xy_step, ::xy_step]
            sub_h, sub_w = sub_arr.shape
            downsampled[i, :sub_h, :sub_w] = sub_arr
            volume_progress = int((i / z_dim) * 90) # up to 90% during processing
            
        p2, p98 = np.percentile(downsampled, (2, 98))
        downsampled = np.clip((downsampled - p2) / (p98 - p2 + 1e-5), 0, 1)
        downsampled = (downsampled * 255).astype(np.uint8)
        
        volume_progress = 100
        
        import io
        buffer = io.BytesIO(downsampled.tobytes())
        from flask import Response
        response = Response(buffer.getvalue(), mimetype='application/octet-stream')
        response.headers['X-Vol-Dim'] = f"{downsampled.shape[2]},{downsampled.shape[1]},{downsampled.shape[0]}"
        return response
    except Exception as e:
        import traceback
        traceback.print_exc()
        volume_progress = -1
        return jsonify({'error': str(e)}), 500

@app.route('/api/points_all')
def get_points_all():
    df = volume_data['centroids']
    if df.empty:
        return jsonify([])
        
    num_slices = volume_data['num_slices']
    h, w = volume_data['shape']
    z_step = max(1, num_slices // 64)
    xy_step = max(1, w // 128)
    
    points = [{'x': row['x']/xy_step, 'y': row['y']/xy_step, 'z': row['z']/z_step, 'r': row['r']} for _, row in df.iterrows()]
    return jsonify(points)

if __name__ == '__main__':
    # Run locally on port 5050
    app.run(host='0.0.0.0', port=5050, debug=True)
