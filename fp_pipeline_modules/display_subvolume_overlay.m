function display_subvolume_overlay(V_raw, V_recon, num_slices, d)
% Show 5 evenly-spaced Z-slices with magenta vessel overlay for a subvolume.

z_show = round(linspace(1, num_slices, min(5, num_slices)));
nc     = numel(z_show);

figure('Name', sprintf('Quadrant %d - Raw with Recon Overlay', d), ...
       'Position', [40 + d*20, 60 + d*20, min(1600, nc*320), 340], 'Visible', 'on');

for si = 1:nc
    z      = z_show(si);
    sl_raw = double(V_raw(:,:,z));
    m      = max(sl_raw(:));
    if m > 0
        sl_raw = sl_raw ./ m;
    end
    
    sl_recon = V_recon(:,:,z);

    % Magenta highlight for reconstructed vessel regions
    R = sl_raw;  G = sl_raw;  B = sl_raw;
    mask = sl_recon > 0;
    R(mask) = 1;  G(mask) = 0;  B(mask) = 1;

    subplot(1, nc, si);
    imshow(cat(3, R, G, B));
    title(sprintf('Q%d Z = %d', d, z), 'FontSize', 8);
end
sgtitle(sprintf('Quadrant %d - Raw Volume with Reconstructed Overlay', d));
drawnow;
end

% -------------------------------------------------------------------------
