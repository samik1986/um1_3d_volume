% Define volume size
volSize = [100, 100, 100];
V = zeros(volSize);

% Define starting and ending coordinates for an arbitrary 3D oblique line: [x, y, z]
P1 = [10, 20, 15];
P2 = [90, 85, 95];

num_points = 300; % Number of points to interpolate
x_line = linspace(P1(1), P2(1), num_points);
y_line = linspace(P1(2), P2(2), num_points);
z_line = linspace(P1(3), P2(3), num_points);

% Combine and round to nearest integer for voxel indices
points = round([x_line', y_line', z_line']);
points = unique(points, 'rows');

% Set voxel values
for i = 1:size(points, 1)
    x = points(i, 1);
    y = points(i, 2);
    z = points(i, 3);
    
    % Ensure indices are within bounds
    x(x < 1) = 1; x(x > volSize(1)) = volSize(1);
    y(y < 1) = 1; y(y > volSize(2)) = volSize(2);
    z(z < 1) = 1; z(z > volSize(3)) = volSize(3);
    
    % Set the corresponding voxels to 1
    idx = sub2ind(volSize, x, y, z);
    V(idx) = 1;
end

% Visualize using 3D scatter plot
figure('Name', 'Original 3D Line');
[y_pts, x_pts, z_pts] = ind2sub(volSize, find(V));
scatter3(x_pts, y_pts, z_pts, 30, 'r', 'filled');

% Adjust view
view(3);
axis equal;
axis([0 volSize(1) 0 volSize(2) 0 volSize(3)]);
xlabel('X'); 
ylabel('Y'); 
zlabel('Z');
title('3D Volume with an Oblique Line');
grid on;
box on;

%% --- New Section: Reconstruction using multiple projections ---
% Take pictures at 5 degree intervals to create gradual stereo pairs across 180 deg
disp('Taking Gradual Stereo Volume Pictures...');
recon_angles = 0:5:180;
recon_pictures = take_volume_pictures(V, recon_angles, 'Y');

% Reconstruct the 3D volume from the pictures
disp('Reconstructing Volume...');
Reconstructed_V = reconstruct_volume(recon_pictures, recon_angles, 'Y', volSize);

% Visualize the original and newly reconstructed 3D volumes
figure('Name', 'Multi-Angle Reconstruction Overlay');
hold on;

% Plot Original Line in Red
[y_orig, x_orig, z_orig] = ind2sub(volSize, find(V));
s1 = scatter3(x_orig, y_orig, z_orig, 50, 'r', 'filled', 'MarkerFaceAlpha', 0.5);

% Plot Reconstructed Line in Blue
[y_recon, x_recon, z_recon] = ind2sub(volSize, find(Reconstructed_V));
if ~isempty(x_recon)
    s2 = scatter3(x_recon, y_recon, z_recon, 30, 'b', 'filled');
    legend([s1, s2], {'Original Line', 'Reconstructed Line'});
    title('Overlay: Original (Red) vs Multi-Angle Reconstructed (Blue)');
else
    legend(s1, {'Original Line (None Reconstructed)'});
    title('Overlay: Original Line ONLY (Reconstruction Failed)');
end

view(3); 
axis equal;
axis([0 volSize(1) 0 volSize(2) 0 volSize(3)]);
xlabel('X'); ylabel('Y'); zlabel('Z');
grid on;
box on;
hold off;

% Save overlay frame
saveas(gcf, 'C:\Users\banerjee\.gemini\antigravity\brain\30d2e639-d822-4229-abed-ca661719e24d\qa_volume_overlay.png');

% Calculate the absolute difference between the two volumes
Diff_V = abs(V - Reconstructed_V);
num_original_voxels = sum(V(:));
num_reconstructed_voxels = sum(Reconstructed_V(:));
num_error_voxels = sum(Diff_V(:));

fprintf('\n--- Reconstruction Stats ---\n');
fprintf('Original Voxels: %d\n', num_original_voxels);
fprintf('Reconstructed Voxels: %d\n', num_reconstructed_voxels);
fprintf('Differing Voxels (Error): %d\n', num_error_voxels);
fprintf('Error Rate vs Original: %.2f%%\n', (num_error_voxels / num_original_voxels) * 100);
