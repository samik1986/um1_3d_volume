function downsample_volumes()
% DOWNSAMPLE_VOLUMES
% Downsamples FP.tif and FP_reconstructed_skeleton.nrrd by factor of 2 in XY only.
% Z dimension is NOT downsampled.
% FP.tif is converted to uint8.

script_dir = fileparts(mfilename('fullpath'));
input_tif  = fullfile(script_dir, 'FP.tif');
input_nrrd = fullfile(script_dir, 'fp_pipeline_output', 'FP_reconstructed_skeleton.nrrd');

output_tif_nrrd  = fullfile(script_dir, 'fp_pipeline_output', 'FP_downsampled_uint8.nrrd');
output_skel_nrrd = fullfile(script_dir, 'fp_pipeline_output', 'FP_reconstructed_skeleton_down2.nrrd');

if ~exist(fullfile(script_dir, 'fp_pipeline_output'), 'dir')
    mkdir(fullfile(script_dir, 'fp_pipeline_output'));
end

%% ---- Task 1: Downsample FP.tif (XY only) ---------------------------------
fprintf('\n== Task 1: Downsampling FP.tif (XY only, to uint8 NRRD) ==\n');
if exist(input_tif, 'file')
    info = imfinfo(input_tif);
    H = info(1).Height;
    W = info(1).Width;
    D = numel(info);
    fprintf('   Original: %d x %d x %d\n', H, W, D);
    
    H2 = floor(H/2); W2 = floor(W/2);
    V_down = zeros(H2, W2, D, 'uint8');
    
    % Find global max for normalization (approximate from first 50 slices)
    fprintf('   Estimating normalization range...\n');
    max_val = 0;
    for z = 1:min(50, D)
        sl = single(imread(input_tif, z));
        max_val = max(max_val, max(sl(:)));
    end
    if max_val == 0, max_val = 1; end
    fprintf('   Using max_val = %.1f for uint8 scaling\n', max_val);

    fprintf('   Processing slices...\n');
    for z = 1:D
        % Read single slice
        sl = single(imread(input_tif, z));
        
        % Downsample XY
        sl_d = imresize(sl, 0.5, 'bilinear');
        
        % Convert to uint8
        sl_u8 = uint8(min(255, (sl_d / max_val) * 255));
        
        % Ensure size match (rounding diffs)
        if size(sl_u8,1) > H2, sl_u8 = sl_u8(1:H2, :); end
        if size(sl_u8,2) > W2, sl_u8 = sl_u8(:, 1:W2); end
        
        V_down(:,:,z) = sl_u8;
        if mod(z, 100) == 0
            fprintf('      Progress: %d / %d slices\n', z, D);
        end
    end
    
    fprintf('   Saving %s...\n', output_tif_nrrd);
    save_nrrd_volume(V_down, output_tif_nrrd, 'uint8');
else
    fprintf('   Warning: %s not found.\n', input_tif);
end

%% ---- Task 2: Downsample FP_reconstructed_skeleton.nrrd (XY only) ---------
fprintf('\n== Task 2: Downsampling FP_reconstructed_skeleton.nrrd (XY only) ==\n');
if exist(input_nrrd, 'file')
    % Based on previous header check: 2720 x 2720 x 331, uint16
    H = 2720; W = 2720; D = 331;
    H2 = floor(H/2); W2 = floor(W/2);
    
    fid = fopen(input_nrrd, 'r', 'l');
    % Skip header (approx 500 bytes, search for \n\n)
    header_found = false;
    header_end_pos = 0;
    while ~feof(fid)
        line = fgets(fid);
        if isempty(strtrim(line)) % \n\n found
            header_end_pos = ftell(fid);
            header_found = true;
            break;
        end
    end
    
    if ~header_found
        fclose(fid);
        error('Could not find NRRD header end.');
    end
    
    V_skel_down = zeros(H2, W2, D, 'uint16');
    fprintf('   Original: %d x %d x %d (uint16)\n', H, W, D);
    
    % Read data sequentially
    fseek(fid, header_end_pos, 'bof');
    
    fprintf('   Processing raw data slices...\n');
    num_elements_per_slice = W * H;
    for z = 1:D
        % Read single slice of raw data
        chunk = fread(fid, num_elements_per_slice, 'uint16=>uint16');
        
        if numel(chunk) < num_elements_per_slice
            fprintf('      Warning: unexpected EOF at slice %d\n', z);
            break;
        end
        
        % Reshape to [W, H] (X-major)
        sl = reshape(chunk, [W, H]);
        
        % Downsample XY (nearest)
        sl_d = imresize(sl, 0.5, 'nearest');
        
        % Ensure size match
        if size(sl_d,1) > W2, sl_d = sl_d(1:W2, :); end
        if size(sl_d,2) > H2, sl_d = sl_d(:, 1:H2); end
        
        V_skel_down(:,:,z) = sl_d;
        
        if mod(z, 100) == 0
            fprintf('      Progress: %d / %d slices\n', z, D);
        end
    end
    fclose(fid);
    
    % Permute back to Y, X, Z for save_nrrd_volume (which permutes it again to X, Y, Z)
    V_final = permute(V_skel_down, [2, 1, 3]); % -> [H2, W2, D]
    
    fprintf('   Saving %s...\n', output_skel_nrrd);
    save_nrrd_volume(V_final, output_skel_nrrd, 'uint16');
else
    fprintf('   Warning: %s not found.\n', input_nrrd);
end

fprintf('\n=== XY-ONLY DOWNSAMPLING COMPLETE ===\n');
end

% -------------------------------------------------------------------------
function save_nrrd_volume(vol, filename, type_str)
fid = fopen(filename, 'w', 'l');
if fid < 0
    warning('Could not open %s for writing.', filename);
    return;
end
vol_p = permute(vol, [2, 1, 3]);
fprintf(fid, 'NRRD0004\n');
fprintf(fid, 'type: %s\n', type_str);
fprintf(fid, 'dimension: 3\n');
fprintf(fid, 'space: left-posterior-superior\n');
fprintf(fid, 'sizes: %d %d %d\n', size(vol_p, 1), size(vol_p, 2), size(vol_p, 3));
fprintf(fid, 'space directions: (1,0,0) (0,1,0) (0,0,1)\n');
fprintf(fid, 'kinds: domain domain domain\n');
fprintf(fid, 'endian: little\n');
fprintf(fid, 'encoding: raw\n');
fprintf(fid, 'space origin: (0,0,0)\n');
fprintf(fid, '\n');
fwrite(fid, vol_p, type_str);
fclose(fid);
fprintf('   Saved: %s\n', filename);
end
