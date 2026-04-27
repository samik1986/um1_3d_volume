function volshow_cells_subset()
    % VOLSHOW_CELLS_SUBSET Overlays detected full cell bodies on intensity volume using volshow.
    
    input_file = 'FP_subset_512.tif';
    fprintf('Loading volume from %s...\n', input_file);
    
    % Load intensity volume
    info = imfinfo(input_file);
    num_slices = numel(info);
    h = info(1).Height;
    w = info(1).Width;
    V = zeros(h, w, num_slices, 'uint16');
    for z = 1:num_slices
        V(:,:,z) = imread(input_file, z);
    end
    V = single(V);
    
    % Step 1: Detect cells to get the full mask
    fprintf('Step 1: Re-detecting cells to generate full masks...\n');
    V_smooth = imgaussfilt3(V, 15);
    V_max = imregionalmax(V_smooth);
    thresh = quantile(V_smooth(:), 0.98); 
    
    % The "Full Cell" is the connected component around the maxima
    % We'll use the thresholded smoothed volume as the mask
    detected_mask = (V_smooth > thresh);
    
    % Label the mask so volshow treats it as distinct objects
    L = uint8(bwlabeln(detected_mask));
    
    % Step 2: volshow visualization
    fprintf('Step 2: Launching volshow with overlay...\n');
    
    % Create a figure but volshow typically opens its own app-like window
    % We will save a screenshot of the volshow result if possible, 
    % though volshow is highly interactive.
    
    % Note: volshow might not support 'OverlayData' in older versions, 
    % but in modern MATLAB it does. 
    % Alternatively, we can show them side-by-side or as a composite.
    
    try
        % Standard modern approach for labeled overlay
        viewer = volshow(V, 'OverlayData', L, 'Config', 'VolumeRendering');
        viewer.OverlayAlphamap = linspace(0, 0.5, 256); % Make label overlay slightly transparent
        
        fprintf('volshow window launched. Please interact with the window.\n');
        
        % For the purpose of this task, we will attempt to capture the frame
        pause(5); % Give it time to render
        % Note: snapnow or getframe might not work easily with volshow's UI
    catch ME
        fprintf('volshow error or version mismatch: %s\n', ME.message);
        fprintf('Falling back to a categorical volume rendering...\n');
        % Fallback: composite volume
        volshow(L > 0);
    end
    
    % To provide a permanent result for the user in this session:
    saveas(gcf, 'volshow_snapshot_attempt.png');
end
