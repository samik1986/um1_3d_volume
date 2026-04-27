% RECONSTRUCT_LINE_FROM_ENDPOINTS
% Explicitly calculates and reconstructs a geometric 3D line boundary strictly 
% by isolating and matching projection tracking on its dual Endpoints.

clear; clc; close all;

%% 1. Configuration 
volSize = [100, 100, 100];
angles = 0:10:180; % Stereo rotation properties

% Define the original boundary points governing the rigid trace line
start_pt = [20, 20, 20];
end_pt = [80, 80, 80];

%% 2. Process Isolated Stereo Dynamics for Start Point
fprintf('--- Process Start Point: (%d, %d, %d) ---\n', start_pt(1), start_pt(2), start_pt(3));
V_start = create_point_volume(volSize, start_pt);
pics_start = take_volume_pictures(V_start, angles, 'Y');
Recon_V_start = reconstruct_single_point(pics_start, angles, volSize);
[x_start_recon, y_start_recon, z_start_recon] = ind2sub(volSize, find(Recon_V_start));
recon_start_pt = [round(mean(x_start_recon)), round(mean(y_start_recon)), round(mean(z_start_recon))];

%% 3. Process Isolated Stereo Dynamics for End Point
fprintf('--- Process End Point: (%d, %d, %d) ---\n', end_pt(1), end_pt(2), end_pt(3));
V_end = create_point_volume(volSize, end_pt);
pics_end = take_volume_pictures(V_end, angles, 'Y');
Recon_V_end = reconstruct_single_point(pics_end, angles, volSize);
[x_end_recon, y_end_recon, z_end_recon] = ind2sub(volSize, find(Recon_V_end));
recon_end_pt = [round(mean(x_end_recon)), round(mean(y_end_recon)), round(mean(z_end_recon))];

%% 4. Trace & Overlay Visualization
fig_overlay = figure('Name', 'Dual-Endpoint Line Reconstruction Overlay', 'Position', [200, 200, 800, 800]);
hold on; grid on; box on; view(3);
axis([0 volSize(1) 0 volSize(2) 0 volSize(3)]);
xlabel('X (Row)'); ylabel('Y (Col)'); zlabel('Z (Depth)');
title('Endpoint Derived Line Overlay: Original (Red) vs Reconstructed (Blue)');

% Overlay Native Target Extrapolation
orig_line_X = [start_pt(1), end_pt(1)];
orig_line_Y = [start_pt(2), end_pt(2)];
orig_line_Z = [start_pt(3), end_pt(3)];
plot3(orig_line_X, orig_line_Y, orig_line_Z, 'r', 'LineWidth', 4);

% Overlay Exact Stereo Geometry Reconstructed Track
recon_line_X = [recon_start_pt(1), recon_end_pt(1)];
recon_line_Y = [recon_start_pt(2), recon_end_pt(2)];
recon_line_Z = [recon_start_pt(3), recon_end_pt(3)];
plot3(recon_line_X, recon_line_Y, recon_line_Z, 'b', 'LineWidth', 2, 'LineStyle', '--');

legend('Original Line Target', 'Reconstructed Endpoint Match', 'Location', 'best');
hold off;

% Complete Process Console Metrics
fprintf('\n======================================================\n');
fprintf('Endpoint Line Vector Mathematical Summary\n');
fprintf('======================================================\n');
fprintf('  Original Vector:       [%d, %d, %d] -> [%d, %d, %d]\n', start_pt, end_pt);
fprintf('  Reconstructed Vector:  [%d, %d, %d] -> [%d, %d, %d]\n', recon_start_pt, recon_end_pt);
orig_len = norm(end_pt - start_pt);
recon_len = norm(recon_end_pt - recon_start_pt);
fprintf('  Original Length:       %.3f pixels\n', orig_len);
fprintf('  Reconstructed Length:  %.3f pixels\n', recon_len);
fprintf('======================================================\n');

saveas(fig_overlay, 'C:\Users\banerjee\qa_line_endpoint_overlay.png');
disp('Execution Complete. Unified Line geometric projection saved.');
