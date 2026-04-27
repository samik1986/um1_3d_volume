% Samik Banerjee
% 03/10/2026

% 3D Volume Vesselness using Multi-Angle MIPs & Frangi Filters
% Target: 32 GB RAM limit, 2700 x 2700 x 201 volume.
% 1. Read 3D TIFF (Memory efficient)
% 2. Take Camera locations 0 to 50 degrees (10 deg intervals)
% 3. Calculate MIPs at each angle
% 4. Clip (>500 = 500) & Normalize
% 5. FrangiFilter2D on MIPs
% 6. Depth from Disparity (Back-projection)

function process_vesselness_3d()
% --- Configuration ---
input_tiff  = 'FP.tif'; % Replace with your file
output_tiff = 'FP_det.tif';

angles = 0:10:50; % 0 to 50 degrees
clip_val = 500;

% Get TIFF info without loading the whole file into RAM
fprintf('Reading TIFF Header...\n');
info = imfinfo(input_tiff);
num_slices = numel(info);
height = info(1).Height;
width = info(1).Width;

fprintf('Volume dimensions: %d x %d x %d\n', height, width, num_slices);

% We need to create the output volume. Since we map back to the same
% 3D space, we will accumulate vesselness scores across angles.
% To save RAM while accumulating, we use single precision, or we write
% to a memory-mapped file or incrementally write.
% 2700*2700*201 * 4 bytes (single) ? 5.8 GB.
% This easily fits in 32GB RAM! We can safely allocate the final output.

% Accumulator for projected vesselness
Vesselness3D = zeros(height, width, num_slices, 'single');

for a = 1:length(angles)
    theta = angles(a);
    fprintf('\nProcessing Angle: %d degrees\n', theta);

    % 1. Compute MIP at angle 'theta' and record Depth (Z-index of max)
    [MIP, DepthMap] = compute_mip_angle(input_tiff, info, theta);

    % 2. Clip and Normalize
    MIP(MIP > clip_val) = clip_val;
    MIP_norm = single(MIP) ./ single(clip_val); % Normalize to 0-1
    imwrite(MIP_norm, ['MIP_' num2str(theta) '.jpg']);
    % 3. Apply Frangi Filter 2D (Using MATLAB native fibermetric)
    fprintf('  -> Applying fibermetric (Frangi Filter 2D)...\n');
    
    MIP_norm_g = imgaussfilt(MIP_norm, 5);
    sigma = [3 5 7];
    vesselness = fibermetric(MIP_norm_g, sigma, 'StructureSensitivity', 0.01);

    % Normalize the result for better thresholding
    vesselness = mat2gray(vesselness);

    % 3. Segmentation (Thresholding to binary image)
    % Use imbinarize or manually pick a threshold based on histogram
    BW = imbinarize(vesselness, 'adaptive');

    % Clean up noise
    BW = bwareaopen(BW, 100); % Remove small artifacts
    BW = imclose(BW, strel('disk', 5)); % Close gaps in neurons

    % 4. Skeletonization
    skeleton = bwskel(BW, 'MinBranchLength', 30);
    imwrite(skeleton, ['Vess2d_' num2str(theta) '.jpg']);

    ovr = imoverlay(MIP_norm, skeleton, 'm');
    imwrite(ovr, ['Skel_' num2str(theta) '.jpg'])
    % 4. Project back to 3D space using the DepthMap
    fprintf('  -> Back-projecting to 3D Volume...\n');
    Vesselness3D = backproject_to_3d(Vesselness3D, skeleton, DepthMap, theta);
end

% 5. Normalize Final 3D Volume
fprintf('\nNormalizing Final 3D Volume...\n');
max_v = max(Vesselness3D(:));
if max_v > 0
    Vesselness3D = Vesselness3D / max_v;
end

% Keep precision to uint16 or uint8 for disk
Vesselness3D_uint16 = uint16(Vesselness3D * 65535);

% 6. Save as multipage TIFF
fprintf('Saving Output TIFF...\n');
save_multipage_tiff(Vesselness3D_uint16, output_tiff);

fprintf('Processing Complete!\n');
end

% -------------------------------------------------------------------------
% Helper Functions
% -------------------------------------------------------------------------

function [MIP, DepthMap] = compute_mip_angle(tif_path, info, theta_deg)
% Computes MIP by rotating the volume.
% Since loading 2700x2700x201 (~1.4 billion pixels) as uint16 is ~2.8 GB,
% we CAN load the volume entirely into RAM on a 32GB system,
% but rotating a 2.8GB volume creates a massive intermediate array.
% To be safe, we compute the projection mathematically using inverse mapping
% or loop slice by slice.

height = info(1).Height;
width = info(1).Width;
num_slices = numel(info);

MIP = zeros(height, width, 'single');
DepthMap = zeros(height, width, 'uint16'); % Stores the Z-index (slice number)

% Math for Rotation around X axis (assuming Y changes, X stays same)
% Or Rotation around Y axis (assuming X changes, Y stays same)
% Let's assume rotation around the Y-axis (Camera moves horizontally)
theta_rad = deg2rad(theta_deg);
cos_t = cos(theta_rad);
sin_t = sin(theta_rad);

x_center = width / 2;
z_center = num_slices / 2;

fprintf('  -> Reading slices and building MIP... ');

% We process slice by slice to save memory.
% For each voxel in the current slice, compute its projected (X,Y) coordinate
% on the camera plane.
for z = 1:num_slices
    if mod(z, 20) == 0, fprintf('%d..', z); end

    slice_data = single(imread(tif_path, z));

    % Relative Z coordinate
    z_rel = z - z_center;

    % Find where this entire slice maps to the camera view
    % For every X in the original slice
    X_orig = 1:width;
    X_rel = X_orig - x_center;

    % Projected X onto the camera sensor
    X_proj = X_rel .* cos_t - z_rel .* sin_t;
    X_proj_idx = round(X_proj + x_center);

    % Create a mask of valid projected X coordinates
    valid_x = (X_proj_idx >= 1) & (X_proj_idx <= width);

    % Instead of doing nested loops, we vectorize over Y and X.
    % Since Y is unaffected by Y-axis rotation, Y maps to Y.

    % For every valid X
    valid_orig_X = X_orig(valid_x);
    valid_proj_X = X_proj_idx(valid_x);

    for k = 1:length(valid_orig_X)
        ox = valid_orig_X(k);
        px = valid_proj_X(k);

        % Grab the entire column (all Ys for this X)
        col_data = slice_data(:, ox);

        % Current maxes at projected X
        curr_max = MIP(:, px);

        % Update MIP where incoming data is greater
        update_mask = col_data > curr_max;
        MIP(update_mask, px) = col_data(update_mask);
        DepthMap(update_mask, px) = z; % Record the slice z that caused the max
    end
end
fprintf('Done.\n');
end

function Vol = backproject_to_3d(Vol, vessel_2d, DepthMap, theta_deg)
% We take the 2D vesselness map and map its pixels back to the 3D
% voxel that caused it (using DepthMap).

[height, width] = size(vessel_2d);
num_slices = size(Vol, 3);

theta_rad = deg2rad(theta_deg);
cos_t = cos(theta_rad);
sin_t = sin(theta_rad);

x_center = width / 2;
z_center = num_slices / 2;

% Vectorized approach for back-projection
for px = 1:width
    % Unique slices responsible for this projected column X
    unique_z = unique(DepthMap(:, px));
    unique_z(unique_z == 0) = []; % Remove 0 (unmapped pixels)

    if isempty(unique_z)
        continue;
    end

    for idx = 1:length(unique_z)
        z = unique_z(idx);
        % Find all Ys in this column that came from slice z
        y_indices = find(DepthMap(:, px) == z);

        % We know the camera pixel (px, y), we know the slice (z).
        % We need to find the original source X.
        z_rel = double(z - z_center);
        px_rel = double(px - x_center);

        % Inverse of projection: px_rel = ox_rel * cos_t - z_rel * sin_t
        % Therefore: ox_rel * cos_t = px_rel + z_rel * sin_t
        % ox_rel = (px_rel + z_rel * sin_t) / cos_t

        % Handle edge case where cos_t approaches 0 (angle = 90)
        if abs(cos_t) > 1e-6
            ox_rel = (px_rel + z_rel * sin_t) / cos_t;
            ox = round(ox_rel + x_center);

            % If original X is valid, accumulate the vesselness
            if ox >= 1 && ox <= width
                % Max pooling across angles
                curr_vol_vals = Vol(y_indices, ox, z);
                incoming_vessel_vals = vessel_2d(y_indices, px);

                Vol_updates = max(curr_vol_vals, incoming_vessel_vals);
                Vol(y_indices, ox, z) = Vol_updates;
            end
        end
    end
end
end

function save_multipage_tiff(vol, filename)
num_slices = size(vol, 3);

% Set up tiff structure
t = Tiff(filename, 'w');
tagstruct.ImageLength = size(vol, 1);
tagstruct.ImageWidth = size(vol, 2);
tagstruct.Photometric = Tiff.Photometric.MinIsBlack;
if isa(vol, 'uint16')
    tagstruct.BitsPerSample = 16;
    tagstruct.SampleFormat = Tiff.SampleFormat.UInt;
elseif isa(vol, 'uint8')
    tagstruct.BitsPerSample = 8;
    tagstruct.SampleFormat = Tiff.SampleFormat.UInt;
end
tagstruct.SamplesPerPixel = 1;
tagstruct.RowsPerStrip = 16;
tagstruct.PlanarConfiguration = Tiff.PlanarConfiguration.Chunky;
tagstruct.Compression = Tiff.Compression.LZW; % Compress to save disk space

for z = 1:num_slices
    if mod(z, 20) == 0, fprintf('Writing slice %d/%d\n', z, num_slices); end

    if z > 1
        t.writeDirectory(); % start new page
    end

    t.setTag(tagstruct);
    t.write(vol(:,:,z));
end
t.close();
end

% -------------------------------------------------------------------------
% Note: Using MATLAB's native fibermetric function (Image Processing Toolbox)
% which natively implements the Frangi vesselness algorithm.
% -------------------------------------------------------------------------