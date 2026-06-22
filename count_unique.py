import tifffile
import numpy as np

filepath = r'C:\Users\banerjee\Desktop\um1_3d_volume\NEWFP\F0016_barcode.tif'
print(f"Opening {filepath}...")

try:
    unique_set = set()
    with tifffile.TiffFile(filepath) as tif:
        # Some big TIFFs have series instead of pages
        if len(tif.series) > 0 and len(tif.series[0].levels) > 0:
            series = tif.series[0]
            print(f"Found series shape: {series.shape}")
            num_z = series.shape[0] if len(series.shape) > 2 else len(tif.pages)
            for z in range(num_z):
                # Reading z plane
                if len(series.shape) > 2:
                    plane = tif.asarray(key=z)
                else:
                    plane = tif.pages[z].asarray()
                unique_set.update(np.unique(plane))
                if z % 50 == 0:
                    print(f"Processed {z}/{num_z} planes...")
        else:
            num_pages = len(tif.pages)
            print(f"Number of pages: {num_pages}")
            for i, page in enumerate(tif.pages):
                plane = page.asarray()
                unique_set.update(np.unique(plane))
                if i % 50 == 0:
                    print(f"Processed {i}/{num_pages} planes...")
                
    print(f"\nTotal number of unique values: {len(unique_set)}")
    if len(unique_set) < 50:
        print(f"Unique values: {sorted(list(unique_set))}")
    else:
        print(f"First 50 unique values: {sorted(list(unique_set))[:50]}")
except Exception as e:
    print(f"Error: {e}")
