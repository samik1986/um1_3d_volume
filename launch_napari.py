import napari
import sys
from qtpy.QtWidgets import QApplication

app = QApplication.instance() or QApplication([])

print("Initializing Napari viewer...")
viewer = napari.Viewer()

# Spacing: Z=0.500, Y=0.1102, X=0.1102
scale_zyx = (0.500, 0.1102, 0.1102)

file_nuc = r'C:\Users\banerjee\Desktop\um1_3d_volume\NEWFP\F0016_Nuc.tif'
print(f"Loading image from {file_nuc}...")
viewer.open(file_nuc, scale=scale_zyx, name='F0016_Nuc', colormap='blue', blending='additive')

file_barcode = r'C:\Users\banerjee\Desktop\um1_3d_volume\NEWFP\F0016_barcode.tif'
print(f"Loading image from {file_barcode}...")
viewer.open(file_barcode, scale=scale_zyx, name='F0016_barcode', colormap='green', blending='additive')

print("Starting Qt event loop directly...")
app.exec_()
