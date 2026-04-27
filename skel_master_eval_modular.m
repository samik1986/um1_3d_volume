% SKEL_MASTER_EVAL_MODULAR
% Strictly executes seamlessly the fully compartmentalized isolated native mathematical bounding pipeline tracking custom Biological TIFF Arrays smoothly.

clear; clc; close all;

angles = 0:10:180; 

disp('================================================');
disp('   MASTER MODULAR STEREO PIPELINE EXECUTION');
disp('================================================');

% Step 1: Read Volume dynamically natively
V_orig_raw = tiffreadVolume('FP.tif');
disp(['QA Debug: Original TIFF Loaded natively. Type: ', class(V_orig_raw)]);
disp(['QA Debug: Dimensions: ', num2str(size(V_orig_raw))]);

% Normalize explicit geometric bounds preventing noise bounds interference identically
V_norm = double(V_orig_raw) / double(max(V_orig_raw(:)));
V_orig_full = V_norm > 0.1; % Top 90% topological structural binary resolution seamlessly

step_size = ceil(max(size(V_orig_full))/400); % Limit maximum dimensions actively isolating RAM limits natively
if step_size > 1
    disp(['QA Debug: Massive biological array discovered natively. Auto-scaling geometry structurally identically by factor of 1/', num2str(step_size), ' sequentially natively guarding against fatal OutOfMemory exceptions.']);
    V_orig = V_orig_full(1:step_size:end, 1:step_size:end, 1:step_size:end);
else
    V_orig = V_orig_full;
end
volSize = size(V_orig);

% Bypass generic trajectory bounds smoothly
pt1_orig = [NaN, NaN, NaN];
pt2_orig = [NaN, NaN, NaN];

% Step 2: Take volume pictures with stereo vision
disp('Step 2: Securing Extrapolated Camera Orthographic Projections...');
pictures = take_volume_pictures(V_orig, angles, 'Y');

% Step 3: Find start and end points in the stereo images
disp('Step 3: Extracting 2D Principal Bounds (Start/End limits) natively...');
[pts_start_2d, pts_end_2d] = extract_endpoints_from_stereo(pictures);

% Step 4: Reconstruct start and end points to volume using Stereo vision and disparity
disp('Step 4: Abstracting Geometric Depths mathematically natively...');
pic_size = size(pictures{1}');
[recon_pt1, recon_pt2] = reconstruct_endpoints_stereo(pts_start_2d, pts_end_2d, angles, volSize, pic_size);

% Step 5: Reconstruct the line from the reconstructed points
disp('Step 5: Unifying Target Node Output spatial topology paths...');
V_line_recon = create_reconstructed_line_volume(recon_pt1, recon_pt2, volSize);

% Step 6: Overlay original line and reconstructed line
disp('Step 6: Executing Final Integrated Topology Overlay evaluation array...');
fig_overlay = overlay_lines(pt1_orig, pt2_orig, recon_pt1, recon_pt2, volSize);

disp('================================================');
disp('   QA DIAGNOSTICS & PIPELINE EVALUATION COMPLETE');
disp('================================================');

saveas(fig_overlay, 'C:\Users\banerjee\Desktop\um1_3d_volume\qa_modular_skel_overlay.png');
