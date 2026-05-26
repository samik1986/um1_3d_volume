import os
import json
import time
import math
import numpy as np
import cupy as cp
import tifffile
import napari
from zernike_basis_gpu import zernike_spherical_gpu, zernike_radial_gpu

class ZernikeFilterBank:
    def __init__(self, optimal_keys_path, voxel_spacing, z_dim, y_dim, x_dim):
        self.voxel_spacing = voxel_spacing
        self.z_dim = z_dim
        self.y_dim = y_dim
        self.x_dim = x_dim
        self.dV = voxel_spacing[0] * voxel_spacing[1] * voxel_spacing[2]
        self.V = z_dim * y_dim * x_dim
        
        # Load optimal keys
        with open(optimal_keys_path, 'r') as f:
            data = json.load(f)
            
        self.selected_shells = data['selected_shells_n_l']
        self.num_functions = data['num_functions']
        
        print(f"Building Zernike Filter Bank for {self.num_functions} functions...")
        self._build_filter_matrix()
        
    def _build_filter_matrix(self):
        start_time = time.time()
        
        # 1. Build physical coordinates
        dz, dy, dx = self.voxel_spacing
        z_idx, y_idx, x_idx = cp.indices((self.z_dim, self.y_dim, self.x_dim))
        
        z_phys = z_idx.flatten() * dz
        y_phys = y_idx.flatten() * dy
        x_phys = x_idx.flatten() * dx
        
        z_c, y_c, x_c = cp.mean(z_phys), cp.mean(y_phys), cp.mean(x_phys)
        z_shifted = z_phys - z_c
        y_shifted = y_phys - y_c
        x_shifted = x_phys - x_c
        
        r_phys = cp.sqrt(x_shifted**2 + y_shifted**2 + z_shifted**2)
        self.max_radius = float(cp.max(r_phys))
        
        rho = r_phys / self.max_radius
        theta = cp.zeros_like(r_phys)
        mask = r_phys > 0
        theta[mask] = cp.arccos(cp.clip(z_shifted[mask] / r_phys[mask], -1.0, 1.0))
        phi = cp.arctan2(y_shifted, x_shifted)
        
        del x_shifted, y_shifted, z_shifted, r_phys
        cp.get_default_memory_pool().free_all_blocks()
        
        # 2. Build the giant filter matrix Z
        # Shape: (num_functions, V)
        # Using complex64 (8 bytes per element) to aggressively save VRAM
        self.Z_matrix = cp.zeros((self.num_functions, self.V), dtype=cp.complex64)
        self.keys = []
        
        row_idx = 0
        for n, l in self.selected_shells:
            # Radial component
            R_nl = zernike_radial_gpu(n, l, rho).astype(cp.float32)
            norm_factor = math.sqrt((2 * n + 3) / (self.max_radius**3))
            
            # W component (Real)
            W_nl = (R_nl * self.dV * norm_factor)
            
            for m in range(-l, l + 1):
                self.keys.append((n, l, m))
                # Angular component
                Y_lm = zernike_spherical_gpu(l, m, theta, phi).astype(cp.complex64)
                
                # Basis function: W_nl * Y_lm
                # Note: To extract, integral is f * Z*. 
                # So we store the conjugate directly in the filter bank!
                self.Z_matrix[row_idx, :] = cp.conjugate(W_nl * Y_lm)
                row_idx += 1
                
        # Clean up spherical grids from VRAM
        del rho, theta, phi
        cp.get_default_memory_pool().free_all_blocks()
        
        end_time = time.time()
        print(f"Filter Bank compiled in {end_time - start_time:.2f} seconds.")
        print(f"Filter Matrix shape: {self.Z_matrix.shape}")
        
    def extract(self, intensity_vol):
        """
        Extract the shape descriptors INSTANTANEOUSLY via a single matrix multiplication.
        """
        if intensity_vol.shape != (self.z_dim, self.y_dim, self.x_dim):
            raise ValueError("Input volume dimensions must strictly match the filter bank!")
            
        print("Extracting descriptors...")
        start_time = time.time()
        
        f_flat = cp.asarray(intensity_vol, dtype=cp.float32).flatten()
        
        # A SINGLE HARDWARE MATRIX-VECTOR MULTIPLICATION!
        # C = Z* @ f
        C_vector = cp.matmul(self.Z_matrix, f_flat)
        
        end_time = time.time()
        print(f">>> Instant Extraction Time: {end_time - start_time:.4f} seconds <<<")
        
        # Pull back to CPU and map to keys
        C_cpu = C_vector.get()
        moments = {self.keys[i]: complex(C_cpu[i]) for i in range(self.num_functions)}
        
        return moments, C_vector

    def reconstruct(self, C_vector):
        """
        Reconstruct the 3D volume INSTANTANEOUSLY via Matrix cross-multiplication.
        """
        print("Reconstructing volume from descriptors...")
        start_time = time.time()
        
        # Z_matrix stores (Z_nlm * dV)^*. 
        # So true Z_nlm is conj(Z_matrix) / dV.
        # We want sum(C_i * Z_i) -> C_vector @ conj(Z_matrix) / dV
        f_recon_flat_complex = cp.matmul(C_vector, cp.conjugate(self.Z_matrix)) / self.dV
        f_recon_flat = cp.real(f_recon_flat_complex)
        
        end_time = time.time()
        print(f">>> Instant Reconstruction Time: {end_time - start_time:.4f} seconds <<<")
        
        return f_recon_flat.reshape((self.z_dim, self.y_dim, self.x_dim)).get()

def main():
    target = 'crop_001_ch04'
    base_dir = r'c:\Users\banerjee\Desktop\um1_3d_volume\neuron_processing\output\custom_crops'
    tif_path = os.path.join(base_dir, f'{target}.tif')
    optimal_keys_path = os.path.join(base_dir, 'optimal_basis_keys.json')
    
    # 1. Load image
    print(f"Loading {tif_path}...")
    vol = tifffile.imread(tif_path)
    
    # 2. Build filter bank (happens once per biological pipeline)
    voxel_spacing = (0.5, 0.1102, 0.1102)
    filter_bank = ZernikeFilterBank(
        optimal_keys_path, 
        voxel_spacing, 
        z_dim=vol.shape[0], 
        y_dim=vol.shape[1], 
        x_dim=vol.shape[2]
    )
    
    # 3. INSTANT EXTRACTION
    moments, C_vector = filter_bank.extract(vol)
    
    # 4. INSTANT RECONSTRUCTION
    recon_vol = filter_bank.reconstruct(C_vector)
    
    # Prove it worked via Metrics
    orig_flat = vol.flatten()
    recon_flat = recon_vol.flatten()
    mse = np.mean((orig_flat - recon_flat)**2)
    r = np.corrcoef(orig_flat, recon_flat)[0, 1]
    
    print("\n========================================")
    print("  Filtered Reconstruction Verification")
    print("========================================")
    print(f"Mean Squared Error     : {mse:.4f}")
    print(f"Pearson Correlation    : {r:.4f}")
    print("========================================\n")
    
    # 5. Napari Visualization
    print("Opening Napari to show results (blocking)...")
    viewer = napari.Viewer()
    scale = voxel_spacing
    
    viewer.add_image(vol, name='Original ch04', colormap='gray', scale=scale, blending='additive')
    viewer.add_image(recon_vol, name='Filtered (Top 99% Energy)', colormap='magma', scale=scale, blending='additive')
    
    napari.run()

if __name__ == '__main__':
    main()
