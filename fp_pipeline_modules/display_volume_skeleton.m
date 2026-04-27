function display_volume_skeleton(ReconFull, num_slices)
% Show 5 evenly-spaced Z-slices with magenta vessel overlay,
% plus a sub-sampled 3D scatter plot.

z_show = round(linspace(1, num_slices, min(5, num_slices)));
nc     = numel(z_show);

figure('Name', 'Full Volume - Skeleton Overlay (Slices)', ...
       'Position', [40, 60, min(1600, nc*320), 340], 'Visible', 'on');

for si = 1:nc
    z    = z_show(si);
    sl_n = mat2gray(double(ReconFull(:,:,z)));      % always double for mat2gray

    % Magenta highlight for reconstructed vessel regions
    R = sl_n;  G = sl_n;  B = sl_n;
    mask = sl_n > 0.45;
    R(mask) = 1;  G(mask) = 0;  B(mask) = 1;

    subplot(1, nc, si);
    imshow(cat(3, R, G, B));
    title(sprintf('Z = %d', z), 'FontSize', 8);
end
sgtitle('Reconstructed Volume - Magenta = Detected Vessel');

% 3D scatter (sub-sampled to <= 20 000 points)
fprintf('   Generating 3D scatter view...\n');
thresh = 0.3;
[rx, ry, rz] = ind2sub(size(ReconFull), find(ReconFull > thresh));
max_pts = 20000;
if numel(rx) > max_pts
    idx = randperm(numel(rx), max_pts);
    rx = rx(idx);  ry = ry(idx);  rz = rz(idx);
end

figure('Name', '3D Vessel Scatter - Full Volume', ...
       'Position', [120, 120, 900, 700], 'Visible', 'on');
scatter3(double(ry), double(rx), double(rz), 2, double(rz), 'filled');
colormap(jet);  colorbar;
xlabel('X (col)');  ylabel('Y (row)');  zlabel('Z (slice)');
title('3D Reconstructed Vessel Skeleton - Full Volume');
axis tight;  grid on;  box on;  view(3);
drawnow;
end

% -------------------------------------------------------------------------
