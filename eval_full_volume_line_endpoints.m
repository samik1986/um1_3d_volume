% EVAL_FULL_VOLUME_LINE_ENDPOINTS
% Resolves an overarching 3D line geometrically by extracting and matching  
% its projected dual end topologies from continuous 2D planar rotation frames.

clear; clc; close all;

%% 1. Create a volume containing the full structural line
volSize = [100, 100, 100];
angles = 0:10:180; 

% Defined original 3D geometry constraints
pt1_orig = [20, 20, 20];
pt2_orig = [80, 80, 80];

V = zeros(volSize);
num_points_line = max(abs(pt2_orig - pt1_orig)) * 2;
X_line = round(linspace(pt1_orig(1), pt2_orig(1), num_points_line));
Y_line = round(linspace(pt1_orig(2), pt2_orig(2), num_points_line));
Z_line = round(linspace(pt1_orig(3), pt2_orig(3), num_points_line));

for k = 1:length(X_line)
    if X_line(k)>=1 && X_line(k)<=volSize(1) && ...
       Y_line(k)>=1 && Y_line(k)<=volSize(2) && ...
       Z_line(k)>=1 && Z_line(k)<=volSize(3)
        V(X_line(k), Y_line(k), Z_line(k)) = 1;
    end
end

fprintf('1. Generated True Volume containing overarching continuous Diagonal Line.\n');

%% 2. Take volumetric pictures explicitly encompassing the unified line
pictures = take_volume_pictures(V, angles, 'Y');
fprintf('2. Evaluated orthogonal volumetric picture sequences resolving spatial properties.\n');

%% 3 & 4. Extract Endpoints mathematically in 2D and Reconstruct depth
[pad_sizeY, pad_sizeX] = size(pictures{1}');
pad_sizeZ = pad_sizeX; 

cx_img = (pad_sizeX + 1) / 2;
cy_img = (pad_sizeY + 1) / 2;
cz_img = (pad_sizeZ + 1) / 2;

Accum_V_start = zeros(volSize);
Accum_V_end = zeros(volSize);
valid_pairs = 0;

% Initial Tracking anchor targeting to prevent stereoscopic intersection inversion
I1 = pictures{1}';
[ptA, ptB] = find_extremes_2d(I1);
prev_start = ptA; 
prev_end = ptB;

for i = 1:(length(angles) - 1)
    theta1 = angles(i);
    theta2 = angles(i+1);
    theta_diff = deg2rad(theta2 - theta1);
    
    I1 = pictures{i}';
    I2 = pictures{i+1}';
    
    if abs(sin(theta_diff)) < 1e-4, continue; end
    
    [ptA1, ptB1] = find_extremes_2d(I1);
    [ptA2, ptB2] = find_extremes_2d(I2);
    
    % Track bounding boxes cleanly to maintain endpoint identity continuously over rotational shift
    if norm(ptA1 - prev_start) + norm(ptB1 - prev_end) < norm(ptB1 - prev_start) + norm(ptA1 - prev_end)
        c1_start = ptA1(1); r1_start = ptA1(2);
        c1_end   = ptB1(1); r1_end   = ptB1(2);
    else
        c1_start = ptB1(1); r1_start = ptB1(2);
        c1_end   = ptA1(1); r1_end   = ptA1(2);
    end
    
    if norm(ptA2 - [c1_start, r1_start]) + norm(ptB2 - [c1_end, r1_end]) < norm(ptB2 - [c1_start, r1_start]) + norm(ptA2 - [c1_end, r1_end])
        c2_start = ptA2(1); r2_start = ptA2(2);
        c2_end   = ptB2(1); r2_end   = ptB2(2);
    else
        c2_start = ptB2(1); r2_start = ptB2(2);
        c2_end   = ptA2(1); r2_end   = ptA2(2);
    end
    
    prev_start = [c2_start, r2_start];
    prev_end   = [c2_end, r2_end];
    
    valid_pairs = valid_pairs + 1;
    
    % --- Core Reconstruct Module logic isolated for the Start Endpoint ---
    xl_s = c1_start - cx_img; xr_s = c2_start - cx_img;
    zl_s = (xl_s * cos(theta_diff) - xr_s) / sin(theta_diff);
    Sub_V_padded = zeros(pad_sizeX, pad_sizeY, pad_sizeZ);
    ox = round(c1_start); oy = round(r1_start); oz = round(zl_s + cz_img);
    if ox>=1 && ox<=pad_sizeX && oy>=1 && oy<=pad_sizeY && oz>=1 && oz<=pad_sizeZ
        Sub_V_padded(ox, oy, oz) = 1;
    end
    Sub_V_aligned_padded = rotate_and_unpad(Sub_V_padded, theta1, pad_sizeX, pad_sizeY, pad_sizeZ);
    Sub_V_aligned = crop_volume(Sub_V_aligned_padded, pad_sizeX, pad_sizeY, pad_sizeZ, volSize);
    Accum_V_start = Accum_V_start + double(Sub_V_aligned > 0);
    
    % --- Core Reconstruct Module logic isolated for the End Endpoint ---
    xl_e = c1_end - cx_img; xr_e = c2_end - cx_img;
    zl_e = (xl_e * cos(theta_diff) - xr_e) / sin(theta_diff);
    Sub_V_padded = zeros(pad_sizeX, pad_sizeY, pad_sizeZ);
    ox = round(c1_end); oy = round(r1_end); oz = round(zl_e + cz_img);
    if ox>=1 && ox<=pad_sizeX && oy>=1 && oy<=pad_sizeY && oz>=1 && oz<=pad_sizeZ
        Sub_V_padded(ox, oy, oz) = 1;
    end
    Sub_V_aligned_padded = rotate_and_unpad(Sub_V_padded, theta1, pad_sizeX, pad_sizeY, pad_sizeZ);
    Sub_V_aligned = crop_volume(Sub_V_aligned_padded, pad_sizeX, pad_sizeY, pad_sizeZ, volSize);
    Accum_V_end = Accum_V_end + double(Sub_V_aligned > 0);
end

fprintf('3 & 4. Extracted extreme boundaries directly from continuous 2D plane and matched corresponding Reconstructions via Stereoscopic Disparity.\n');

% Line endpoints jitter extremely under slight raster aliasing. Any valid intersection is kept.
vote_threshold = 1;
Recon_start = Accum_V_start >= vote_threshold;
Recon_end   = Accum_V_end >= vote_threshold;

[xs, ys, zs] = ind2sub(volSize, find(Recon_start));
[xe, ye, ze] = ind2sub(volSize, find(Recon_end));
recon_pt1 = [round(mean(xs)), round(mean(ys)), round(mean(zs))];
recon_pt2 = [round(mean(xe)), round(mean(ye)), round(mean(ze))];

%% 5. Overlay original and reconstructed lines in 3D seamlessly
fig_overlay = figure('Name', 'Full Topology Line Tracking Overlay', 'Position', [100, 100, 800, 800]);
hold on; grid on; box on; view(3);
axis([0 volSize(1) 0 volSize(2) 0 volSize(3)]);
xlabel('X (Row)'); ylabel('Y (Col)'); zlabel('Z (Depth)');
title('Full Volume Native Extraction Overlay: Original (Red) vs Reconstructed (Blue)');

plot3([pt1_orig(1), pt2_orig(1)], [pt1_orig(2), pt2_orig(2)], [pt1_orig(3), pt2_orig(3)], 'r', 'LineWidth', 4);
if ~isnan(recon_pt1(1)) && ~isnan(recon_pt2(1))
    plot3([recon_pt1(1), recon_pt2(1)], [recon_pt1(2), recon_pt2(2)], [recon_pt1(3), recon_pt2(3)], 'b--', 'LineWidth', 2);
    
    % Match native legend explicitly ensuring bulletproof graphical mappings
    h1 = scatter3(NaN, NaN, NaN, 100, 'r', 'filled', 'MarkerFaceAlpha', 0.5);
    h2 = plot3([NaN,NaN], [NaN,NaN], [NaN,NaN], 'b--', 'LineWidth', 2);
    legend([h1, h2], {'Original Continuous Target', 'Endpoint Extracted Reconstruction'}, 'Location', 'best');
    
    fprintf('5. Connected explicitly evaluated volumetric boundary ends to map final geometric vectors.\n');
else
    fprintf('FAILED: One or both dynamically extracted stereoscopic endpoints failed robustness criteria mapping.\n');
end
hold off;

saveas(fig_overlay, 'C:\Users\banerjee\Desktop\um1_3d_volume\qa_full_volume_line_overlay.png');
disp('Execution Complete. 2D Frame Topology Line abstraction geometric projection successfully synthesized.');


%% ====== LOCAL PIPELINE HELPER FUNCTIONS ======

function [ptA, ptB] = find_extremes_2d(I)
    % Evaluates native pixel connectivity iteratively calculating extreme spatial components vector
    [r, c] = find(I > 0.1);
    if length(r) < 2
        ptA = [NaN, NaN]; ptB = [NaN, NaN];
        return;
    end
    pts = [c, r];
    mu = mean(pts, 1);
    centered = pts - mu;
    [~, ~, V_svd] = svd(centered, 'econ');
    dir_vec = V_svd(:, 1);
    proj = centered * dir_vec;
    [~, min_idx] = min(proj);
    [~, max_idx] = max(proj);
    ptA = pts(min_idx, :);
    ptB = pts(max_idx, :);
end

function V = rotate_and_unpad(Sub_V_padded, theta1, padX, padY, padZ)
    % Natively orient the tracking accumulation matrices utilizing explicitly rigid nearest interpolation grids
    Sub_V_perm = permute(Sub_V_padded, [1, 3, 2]); 
    Sub_V_rot = imrotate(Sub_V_perm, -theta1, 'nearest', 'crop');
    V = ipermute(Sub_V_rot, [1, 3, 2]); 
end

function V = crop_volume(Sub_V_aligned_padded, padX, padY, padZ, volSize)
    % Precisely isolate central global boundary box from tracking padding envelope limits securely
    px = floor((padX - volSize(1))/2) + 1;
    py = floor((padY - volSize(2))/2) + 1;
    pz = floor((padZ - volSize(3))/2) + 1;
    V = Sub_V_aligned_padded(px : px + volSize(1) - 1, py : py + volSize(2) - 1, pz : pz + volSize(3) - 1);
end
