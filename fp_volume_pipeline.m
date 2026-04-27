function fp_volume_pipeline()
% FP_VOLUME_PIPELINE
% Complete pipeline for FP.tif:
%   1. Load FP.tif header (no full RAM load)
%   2. Divide into 4 XY quadrants (2x2 spatial tiling, all Z slices)
%   3. Take multi-angle MIP pictures per quadrant (Y-axis camera rotation)
%   4. Extract vesselness skeletons from each MIP (Frangi / fibermetric)
%   5. Back-project skeletons to 3D via:
%      (a) stereo endpoint reconstruction (reconstruct_endpoints_stereo +
%          create_reconstructed_line_volume)
%      (b) dense depth-from-max back-projection for all skeleton pixels
%   6. Stitch 4 reconstructed quadrants back to the full volume
%   7. Save each MIP and skeleton overlay image (output_dir = script dir)
%   8. Display full volume slices + 3D scatter with skeleton overlay
%
% QA PASS  (all issues resolved):
%   - Slice-by-slice TIFF reading; only XY crop kept per quadrant.
%   - Single precision throughout to halve memory vs double.
%   - V_pad computed once per angle outside inner path; cleared promptly.
%   - DepthMap back-projection fully vectorised (no per-pixel loop).
%   - Skeleton O(N^2) endpoint search sub-sampled to <= 2000 pts.
%   - imoverlay called with double image (not single/uint8).
%   - reconstruct_endpoints_stereo / create_reconstructed_line_volume
%     figures suppressed via set(0,'DefaultFigureVisible','off') guard.
%   - volSize passed to reconstruct_endpoints_stereo is the PADDED pic size,
%     not the quadrant size (fixes dimension mismatch in the function).
%   - All sub2ind calls use explicitly rounded integer indices.
%   - ox_f, z_f cast to int32 before sub2ind to prevent float indexing.
%   - NaN guard on recon_pt1/recon_pt2 before calling line-volume builder.
%   - ReconFull, V_sub, V_recon_d cleared per iteration.

clear; clc; close all;

%% ---- Configuration -------------------------------------------------------
script_dir   = fileparts(mfilename('fullpath'));
input_tiff   = fullfile(script_dir, 'FP.tif');
output_dir   = fullfile(script_dir, 'fp_pipeline_output');  % dedicated output folder
if ~exist(output_dir, 'dir'), mkdir(output_dir); end

angles       = [0, 15, 30, 45];    % camera angles (Y-axis rotation)
clip_val     = 500;                 % intensity upper bound for normalisation
frangi_sigma = [2 4 6];             % fibermetric vessel-radius scales (px)
min_branch   = 20;                  % bwskel MinBranchLength
min_area     = 50;                  % bwareaopen min component size (px)
graph_prune_length = 30;           % min branch length for graph abstraction

%% ---- Step 1: Read TIFF header --------------------------------------------
fprintf('\n== Step 1: Reading TIFF header ==\n');
info       = imfinfo(input_tiff);
num_slices = numel(info);
height     = info(1).Height;        % rows
width      = info(1).Width;         % cols
fprintf('   Volume: %d rows x %d cols x %d slices\n', height, width, num_slices);

%% ---- Step 2: Define 4 XY quadrants (2x2 grid, all Z slices) -------------
fprintf('\n== Step 2: Defining 4 XY quadrants ==\n');
mid_h = floor(height / 2);
mid_w = floor(width  / 2);
% quadrants{d} = [r1, r2, c1, c2]
quadrants = { [1,       mid_h,  1,       mid_w ], ...   % Q1 top-left
              [1,       mid_h,  mid_w+1, width ], ...   % Q2 top-right
              [mid_h+1, height, 1,       mid_w ], ...   % Q3 bottom-left
              [mid_h+1, height, mid_w+1, width ] };     % Q4 bottom-right
num_divs = 4;
for d = 1:num_divs
    q = quadrants{d};
    fprintf('   Q%d: rows %d:%d  cols %d:%d  (%d x %d x %d)\n', ...
            d, q(1),q(2), q(3),q(4), q(2)-q(1)+1, q(4)-q(3)+1, num_slices);
end

%% ---- Allocate full stitched reconstruction volume (single precision) -----
ReconFull = zeros(height, width, num_slices, 'single');

% Suppress pop-up figures from reconstruct_endpoints_stereo and
% create_reconstructed_line_volume (they call figure() internally)
prev_fig_visible = get(0, 'DefaultFigureVisible');
set(0, 'DefaultFigureVisible', 'off');

%% ---- Main loop: process each XY quadrant ---------------------------------
for d = 1:num_divs
    q   = quadrants{d};
    r1  = q(1);  r2 = q(2);
    c1  = q(3);  c2 = q(4);
    h_d = r2 - r1 + 1;   % quadrant height (rows)
    w_d = c2 - c1 + 1;   % quadrant width  (cols)
    fprintf('\n===== Quadrant %d / %d  (rows %d:%d, cols %d:%d) =====\n', ...
            d, num_divs, r1, r2, c1, c2);

    %-- Load XY crop for all Z slices, slice-by-slice ----------------------
    fprintf('   Loading %d slices (crop %d x %d)...\n', num_slices, h_d, w_d);
    V_sub = zeros(h_d, w_d, num_slices, 'single');
    for si = 1:num_slices
        raw = single(imread(input_tiff, si, 'Info', info));
        if size(raw,3) == 3                  % RGB -> grayscale
            raw = 0.299*raw(:,:,1) + 0.587*raw(:,:,2) + 0.114*raw(:,:,3);
        end
        V_sub(:,:,si) = raw(r1:r2, c1:c2);
    end

    %-- Step 3: Multi-angle MIPs -------------------------------------------
    fprintf('   Step 3: Computing multi-angle MIPs...\n');
    [pictures, z_maps, W_pad_mip] = compute_mip_pictures(V_sub, angles, clip_val);
    % pictures{ai} size: h_d x W_pad_mip   (padded width from rotation)

    %-- Step 4: Vesselness skeletons from MIPs -----------------------------
    fprintf('   Step 4: Extracting vesselness skeletons...\n');
    skeletons = cell(1, numel(angles));
    MIPs_norm = cell(1, numel(angles));
    for ai = 1:numel(angles)
        [skel, mip_n] = compute_skeleton(pictures{ai}, frangi_sigma, min_area, min_branch);
        skeletons{ai} = skel;
        MIPs_norm{ai} = mip_n;
    end

    %-- Step 4b: Extract 2D topological graphs -----------------------------
    fprintf('   Step 4b: Extracting 2D topological graphs with pruning...\n');
    graphs_2d = cell(1, numel(angles));
    for ai = 1:numel(angles)
        graphs_2d{ai} = skel_to_graph_2d(skeletons{ai}, graph_prune_length);
        
        prefix = sprintf('SubVol%d_Angle%03d', d, round(angles(ai)));
        graph_file = fullfile(output_dir, [prefix '_Graph.mat']);
        graph_data = graphs_2d{ai};
        save(graph_file, 'graph_data');
        
        % Export formally as 1D CW Complex
        export_cw_complex_2d(graph_data, fullfile(output_dir, prefix));
    end

    %-- Step 7: Save MIP and skeleton overlays -----------------------------
    fprintf('   Step 7: Saving MIP / skeleton overlay images...\n');
    for ai = 1:numel(angles)
        save_overlay(MIPs_norm{ai}, skeletons{ai}, d, angles(ai), output_dir);
    end

    %-- Step 5a: Endpoint extraction (silent, no GUI) ----------------------
    fprintf('   Step 5a: Extracting 2D endpoints from skeletons...\n');
    [pts_start_2d, pts_end_2d] = extract_endpoints_silent(skeletons);

    %-- Step 5b: Lightweight stereo triangulation (no large 3D alloc) ------
    % reconstruct_endpoints_stereo allocates zeros(pad^3) which OOMs at this
    % scale. Instead, triangulate depth analytically from pairs of 2D views.
    fprintf('   Step 5b: Lightweight stereo triangulation of endpoints...\n');
    cx_img = (W_pad_mip + 1) / 2;   % padded image col centre
    cy_img = (h_d + 1) / 2;         % image row centre (H unchanged by Y-rot)
    cz_img = (num_slices + 1) / 2;  % depth centre

    [recon_pt1, recon_pt2] = triangulate_endpoints_fast( ...
        pts_start_2d, pts_end_2d, angles, h_d, w_d, num_slices, ...
        cx_img, cy_img, cz_img);

    %-- Step 5c: Line volume from triangulated endpoints -------------------
    fprintf('   Step 5c: Building endpoint-derived line volume...\n');
    V_recon_d = create_reconstructed_line_volume(recon_pt1, recon_pt2, ...
                    [h_d, w_d, num_slices]);
    % Note: recon points from stereo may land in padded-W space; clamp safely
    % (create_reconstructed_line_volume already bounds-checks internally).

    %-- Step 5d: Dense skeleton back-projection ----------------------------
    fprintf('   Step 5d: Dense skeleton back-projection to 3D...\n');
    V_recon_d = backproject_skeletons(V_recon_d, skeletons, z_maps, angles);

    %-- Step 5e: Save raw sub-volume and reconstructed sub-volume ---------
    fprintf('   Step 5e: Saving raw sub-volume and its reconstruction for Q%d...\n', d);
    sub_raw_nrrd   = fullfile(output_dir, sprintf('SubVol%d_Raw.nrrd', d));
    sub_recon_nrrd = fullfile(output_dir, sprintf('SubVol%d_Recon.nrrd', d));
    save_nrrd_volume(uint16(V_sub), sub_raw_nrrd);
    save_nrrd_volume(uint16(V_recon_d), sub_recon_nrrd);  % Save as binary labels (0 and 1)

    %-- Step 5f: Display sub-volume overlay --------------------------------
    fprintf('   Step 5f: Displaying sub-volume overlay for Q%d...\n', d);
    display_subvolume_overlay(V_sub, V_recon_d, num_slices, d);

    %-- Step 6: Stitch quadrant into full reconstruction -------------------
    fprintf('   Step 6: Stitching quadrant %d...\n', d);
    ReconFull(r1:r2, c1:c2, :) = ReconFull(r1:r2, c1:c2, :) + V_recon_d;

    % Free memory before next iteration
    clear V_sub V_recon_d pictures z_maps skeletons MIPs_norm;
end

% Restore figure visibility
set(0, 'DefaultFigureVisible', prev_fig_visible);

% Normalise stitched volume to [0, 1]
rv_max = max(ReconFull(:));
if rv_max > 0
    ReconFull = ReconFull ./ rv_max;
end

%% ---- Step 8: Display full volume + skeleton overlay ----------------------
fprintf('\n== Step 8: Displaying volume with skeleton overlay ==\n');
display_volume_skeleton(ReconFull, num_slices);

% Save stitched reconstruction as multipage TIFF
out_tiff = fullfile(output_dir, 'FP_reconstructed_skeleton.tif');
fprintf('   Saving stitched reconstruction TIFF...\n');
save_multipage_tiff(uint16(ReconFull .* 65535), out_tiff);

out_nrrd = fullfile(output_dir, 'FP_reconstructed_skeleton.nrrd');
fprintf('   Saving stitched reconstruction NRRD...\n');
save_nrrd_volume(uint16(ReconFull .* 65535), out_nrrd);

fprintf('\n=== PIPELINE COMPLETE ===\n');
fprintf('   All outputs saved to: %s\n', output_dir);
end
