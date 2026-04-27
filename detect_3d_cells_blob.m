function [centroids, L] = detect_3d_cells_blob()
    % DETECT_3D_CELLS_BLOB Detects biological cell bodies in a 3D volume.
    input_file = 'Q4_bottom_right.tif';
    
    fprintf('Loading volume from %s...\n', input_file);
    V = load_tiff_volume(input_file);
    V = single(V);
    
    % Step 1: 3D Gaussian Smoothing
    % User said cells are < 80px wide. 
    % A sigma of 15-20 should capture these blobs well.
    fprintf('Step 1: Applying 3D Gaussian smoothing (sigma=15)...\n');
    V_smooth = imgaussfilt3(V, 15);
    
    % Step 2: Background Subtraction (optional but helpful)
    % For now, we'll use thresholding on the smoothed volume directly.
    
    % Step 3: Thresholding to get Cell Morphology
    % Find an appropriate threshold to ignore background/vessels
    % We'll use a simple percentile-based threshold for the subset
    thresh = quantile(V_smooth(:), 0.98); 
    fprintf('Step 3: Filtering detections with threshold %.2f...\n', thresh);
    
    cell_mask = V_smooth > thresh;
    
    % Step 4: Extract Centroids and Morphology
    fprintf('Step 4: Extracting morphology, centroids and properties...\n');
    % Use bwconncomp to label individual cell bodies
    CC = bwconncomp(cell_mask);
    stats = regionprops3(CC, 'Centroid', 'Volume', 'VoxelIdxList');
    
    % Filter out very small detections if necessary (e.g. noise)
    valid_idx = stats.Volume >= 1;
    stats = stats(valid_idx, :);
    
    centroids = stats.Centroid;
    fprintf('Detected %d cell candidates.\n', size(centroids, 1));
    
    % Create the labeled volume L
    L = zeros(size(cell_mask), 'uint32');
    for i = 1:height(stats)
        L(stats.VoxelIdxList{i}) = i;
    end
    
    % Save results
    save('cell_detections_subset.mat', 'centroids', 'stats', 'L');
    
    % Step 5: Visualization
    visualize_detections(V, L);
end

function V = load_tiff_volume(filename)
    info = imfinfo(filename);
    num_slices = numel(info);
    h = info(1).Height;
    w = info(1).Width;
    V = zeros(h, w, num_slices, 'uint16');
    for z = 1:num_slices
        V(:,:,z) = imread(filename, z);
    end
end

function visualize_detections(V, L)
    fprintf('Visualizing detections with volumeViewer...\n');
    
    % Use volumeViewer to overlay the labeled volume L on the original volume V
    % Since L is a labeled volume, volumeViewer will treat it as a categorical overlay
    % Add spacing for x, y, z
    volumeViewer(V, L, 'ScaleFactors', [0.1102, 0.1102, 0.5]);
end
