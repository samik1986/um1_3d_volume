function [pictures, z_maps, W_out] = compute_mip_pictures(V, angles, clip_val)
% Analytical slice-by-slice MIP — NO 3D padarray (avoids OOM on large vols).
% Y-axis rotation: for each Z-slice, each original column X maps to a
% projected column X_proj = (X-cx)*cos(t) - (z-cz)*sin(t) + cx.
% Rows (Y dimension) are unaffected by Y-axis rotation.
%
% Returns:
%   pictures{ai}  - H x W_out single MIP image (clipped, normalised)
%   z_maps{ai}    - H x W_out uint16 z-coordinate of the brightest pixel
%   W_out         - output image width (= original W, no padding needed)

[H, W, D] = size(V);
cx = (W + 1) / 2;   % column centre
cz = (D + 1) / 2;   % depth  centre

num_ang  = numel(angles);
W_out    = W;                          % output width stays the same as input
pictures = cell(1, num_ang);
z_maps   = cell(1, num_ang);

% Pre-compute per-angle projection maps (cheap)
col_maps = cell(1, num_ang);   % col_maps{ai}(z, x) -> projected x-index
for ai = 1:num_ang
    theta   = angles(ai);
    cos_t   = cos(deg2rad(theta));
    sin_t   = sin(deg2rad(theta));
    X_orig  = (1:W) - cx;                     % relative original columns
    Z_rel   = (1:D) - cz;                     % relative depth indices
    % Projected col for each (z, x): size D x W
    proj    = bsxfun(@minus, X_orig .* cos_t, Z_rel' .* sin_t) + cx;
    col_maps{ai} = round(proj);               % D x W integer projected cols
end

% Build MIPs: for each angle, iterate slices accumulating max
for ai = 1:num_ang
    mip     = zeros(H, W_out, 'single');
    z_map   = zeros(H, W_out, 'uint16');
    cmap    = col_maps{ai};   % D x W
    for z = 1:D
        slice_data = V(:,:,z);            % H x W single
        px_cols    = cmap(z, :);          % 1 x W projected col indices
        valid      = (px_cols >= 1) & (px_cols <= W_out);
        orig_cols  = find(valid);
        proj_cols  = px_cols(orig_cols);
        if isempty(orig_cols), continue; end
        % For each valid (orig_col -> proj_col) pair, max-pool into MIP
        for k = 1:numel(orig_cols)
            oc = orig_cols(k);
            pc = proj_cols(k);
            upd = slice_data(:, oc) > mip(:, pc);
            mip(upd, pc) = slice_data(upd, oc);
            if any(upd)
                z_map(upd, pc) = z;
            end
        end
    end
    % Clip and normalise
    mip(mip > clip_val) = clip_val;
    m = max(mip(:));
    if m > 0, mip = mip ./ m; end
    pictures{ai} = mip;
    z_maps{ai}   = z_map;
end
end

% -------------------------------------------------------------------------
