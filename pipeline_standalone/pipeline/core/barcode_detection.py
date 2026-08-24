import time
import numpy as np
import tifffile
import scipy.ndimage as ndi
import os

try:
    import cupy as cp
    import cupy_backends
    os.environ["CUDA_PATH"] = os.path.dirname(cupy_backends.__file__)
    import cupyx.scipy.ndimage as cp_ndi
    HAS_GPU = True
except ImportError:
    HAS_GPU = False

def detect_barcodes(image_path, threshold_percentile=99.9):
    print(f"\n--- Detecting Barcodes in {os.path.basename(image_path)} ---")
    t0 = time.time()
    vol = tifffile.imread(image_path)
    
    if HAS_GPU:
        gpu_vol = cp.asarray(vol)
        thresh = cp.percentile(gpu_vol, threshold_percentile)
        gpu_binary = gpu_vol > thresh
        labels_gpu, num_features = cp_ndi.label(gpu_binary)
        binary_out = cp.asnumpy(gpu_binary)
        labels_out = cp.asnumpy(labels_gpu)
        del gpu_vol, gpu_binary, labels_gpu
        cp.get_default_memory_pool().free_all_blocks()
    else:
        thresh = np.percentile(vol, threshold_percentile)
        binary_out = vol > thresh
        labels_out, num_features = ndi.label(binary_out)
        
    print(f"Found {num_features} initial barcode components.")
    
    if num_features > 0:
        slices = ndi.find_objects(labels_out)
        centroids_list = []
        for i, slc in enumerate(slices):
            if slc is not None:
                crop_binary = binary_out[slc]
                crop_labels = labels_out[slc]
                local_com = ndi.center_of_mass(crop_binary, crop_labels, i + 1)
                global_z = slc[0].start + local_com[0]
                global_y = slc[1].start + local_com[1]
                global_x = slc[2].start + local_com[2]
                centroids_list.append([global_z, global_y, global_x])
        centroids = np.array(centroids_list)
    else:
        centroids = np.empty((0,3))
        
    print(f"Barcode detection finished in {time.time()-t0:.2f}s")
    return centroids

def filter_structures(barcodes_555, barcodes_640, soma_mask, neurite_mask, binary_skel, tolerance=10):
    print(f"\n--- Filtering Structures (Tolerance: +-{tolerance} voxels) ---")
    t0 = time.time()
    
    # 0. Remove skeletons from the soma area + 2 pixels
    print("Removing skeletons from the soma area + 2 pixels...")
    if HAS_GPU:
        gpu_soma = cp.asarray(soma_mask)
        struct = cp.ones((3,3,3), dtype=bool)
        for _ in range(2):
            gpu_soma = cp_ndi.binary_dilation(gpu_soma, structure=struct, iterations=1)
        dilated_soma = cp.asnumpy(gpu_soma)
        del gpu_soma
        cp.get_default_memory_pool().free_all_blocks()
    else:
        struct = np.ones((3,3,3), dtype=bool)
        dilated_soma = ndi.binary_dilation(soma_mask, structure=struct, iterations=2)
        
    binary_skel = binary_skel & ~dilated_soma
    
    # 1. Dilate structures by tolerance
    print("Dilating structural mask (skeleton only)...")
    combined_mask = binary_skel
    
    if HAS_GPU:
        gpu_mask = cp.asarray(combined_mask)
        struct = cp.ones((3,3,3), dtype=bool)
        for _ in range(tolerance):
            gpu_mask = cp_ndi.binary_dilation(gpu_mask, structure=struct, iterations=1)
        dilated_mask = cp.asnumpy(gpu_mask)
        del gpu_mask
        cp.get_default_memory_pool().free_all_blocks()
    else:
        struct = np.ones((3,3,3), dtype=bool)
        dilated_mask = ndi.binary_dilation(combined_mask, structure=struct, iterations=tolerance)
        
    # 2. Filter barcodes based on dilated structures
    def filter_bcs(bcs):
        if len(bcs) == 0: return np.empty((0,3)), np.empty((0,3))
        filtered = []
        discarded = []
        for bc in bcs:
            z, y, x = int(round(bc[0])), int(round(bc[1])), int(round(bc[2]))
            z = np.clip(z, 0, dilated_mask.shape[0]-1)
            y = np.clip(y, 0, dilated_mask.shape[1]-1)
            x = np.clip(x, 0, dilated_mask.shape[2]-1)
            if dilated_mask[z, y, x]:
                filtered.append(bc)
            else:
                discarded.append(bc)
        return np.array(filtered) if len(filtered) > 0 else np.empty((0,3)), np.array(discarded) if len(discarded) > 0 else np.empty((0,3))

    filt_555, disc_555 = filter_bcs(barcodes_555)
    filt_640, disc_640 = filter_bcs(barcodes_640)
    print(f"Filtered barcodes: 555 ({len(filt_555)}), 640 ({len(filt_640)})")
    print(f"Discarded barcodes: 555 ({len(disc_555)}), 640 ({len(disc_640)})")
    
    # 3. Filter somas and neurites based on filtered barcodes
    print("Filtering somas, neurites, and skeletons to keep only components near valid barcodes...")
    all_filtered_barcodes = []
    if len(filt_555) > 0: all_filtered_barcodes.extend(filt_555)
    if len(filt_640) > 0: all_filtered_barcodes.extend(filt_640)
    all_filtered_barcodes = np.array(all_filtered_barcodes)
    
    def filter_mask_by_barcodes(mask, valid_bcs):
        if not np.any(mask): return mask
        if len(valid_bcs) == 0: return np.zeros_like(mask)
        
        if HAS_GPU:
            gpu_m = cp.asarray(mask)
            labels, num = cp_ndi.label(gpu_m)
            labels_cpu = cp.asnumpy(labels)
            del gpu_m, labels
            cp.get_default_memory_pool().free_all_blocks()
        else:
            labels_cpu, num = ndi.label(mask)
            
        # Create mask of valid barcodes
        bc_mask = np.zeros_like(mask)
        for bc in valid_bcs:
            z, y, x = int(round(bc[0])), int(round(bc[1])), int(round(bc[2]))
            z = np.clip(z, 0, mask.shape[0]-1)
            y = np.clip(y, 0, mask.shape[1]-1)
            x = np.clip(x, 0, mask.shape[2]-1)
            bc_mask[z, y, x] = True
            
        # Dilate barcodes by tolerance so they overlap with the actual structure
        if HAS_GPU:
            gpu_bc = cp.asarray(bc_mask)
            struct = cp.ones((3,3,3), dtype=bool)
            for _ in range(tolerance):
                gpu_bc = cp_ndi.binary_dilation(gpu_bc, structure=struct, iterations=1)
            bc_mask_dilated = cp.asnumpy(gpu_bc)
            del gpu_bc
            cp.get_default_memory_pool().free_all_blocks()
        else:
            struct = np.ones((3,3,3), dtype=bool)
            bc_mask_dilated = ndi.binary_dilation(bc_mask, structure=struct, iterations=tolerance)
            
        keep_labels = np.unique(labels_cpu[bc_mask_dilated])
        keep_labels = keep_labels[keep_labels > 0]
        
        filtered = np.isin(labels_cpu, keep_labels)
        return filtered

    filtered_neurite_mask = filter_mask_by_barcodes(neurite_mask, all_filtered_barcodes)
    
    # Calculate skeleton mask by masking the original skeleton with the filtered neurites
    filtered_skel_mask = binary_skel & filtered_neurite_mask

    print("Filtering somas by connectivity to retained skeletons...")
    if HAS_GPU:
        gpu_fskel = cp.asarray(filtered_skel_mask)
        struct = cp.ones((3,3,3), dtype=bool)
        for _ in range(2):
            gpu_fskel = cp_ndi.binary_dilation(gpu_fskel, structure=struct, iterations=1)
        dilated_fskel = cp.asnumpy(gpu_fskel)
        del gpu_fskel
        cp.get_default_memory_pool().free_all_blocks()
    else:
        struct = np.ones((3,3,3), dtype=bool)
        dilated_fskel = ndi.binary_dilation(filtered_skel_mask, structure=struct, iterations=2)
        
    if HAS_GPU:
        gpu_soma = cp.asarray(soma_mask)
        labels_soma, _ = cp_ndi.label(gpu_soma)
        labels_soma_cpu = cp.asnumpy(labels_soma)
        del gpu_soma, labels_soma
        cp.get_default_memory_pool().free_all_blocks()
    else:
        labels_soma_cpu, _ = ndi.label(soma_mask)
        
    keep_soma_labels = np.unique(labels_soma_cpu[dilated_fskel])
    keep_soma_labels = keep_soma_labels[keep_soma_labels > 0]
    
    filtered_soma_mask = np.isin(labels_soma_cpu, keep_soma_labels)

    disc_soma_mask = soma_mask & ~filtered_soma_mask
    disc_neurite_mask = neurite_mask & ~filtered_neurite_mask
    disc_skel_mask = binary_skel & ~filtered_skel_mask

    print(f"Structural filtering completed in {time.time()-t0:.2f}s")
    return {
        'filt_555': filt_555, 'disc_555': disc_555,
        'filt_640': filt_640, 'disc_640': disc_640,
        'filt_soma': filtered_soma_mask, 'disc_soma': disc_soma_mask,
        'filt_neurite': filtered_neurite_mask, 'disc_neurite': disc_neurite_mask,
        'filt_skel': filtered_skel_mask, 'disc_skel': disc_skel_mask
    }
