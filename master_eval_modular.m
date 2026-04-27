% MASTER_EVAL_MODULAR
% Strictly executes seamlessly the fully compartmentalized isolated native mathematical bounding pipeline.

clear; clc; close all;

volSize = [100, 100, 100];
pt1_orig = [20, 20, 20];
pt2_orig = [80, 80, 80];

% Stereo sweep setup rigorously expanding native stereoscopic matrices continuously
angles = 0:10:180; 

disp('================================================');
disp('   MASTER MODULAR STEREO PIPELINE EXECUTION');
disp('================================================');

% Step 1: Create Volume with line
disp('Step 1: Generating Original Diagnostic 3D Volume Context...');
[V_orig, pt1_val, pt2_val] = create_line_volume(volSize, pt1_orig, pt2_orig);

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
disp('   PIPELINE COMPLETE - NO ERRORS REPORTED');
disp('================================================');

saveas(fig_overlay, 'C:\Users\banerjee\Desktop\um1_3d_volume\qa_modular_refactored_overlay.png');
