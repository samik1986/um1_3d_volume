function V_recon = backproject_skeletons(V_recon, skeletons, z_maps, angles)
% Slice-by-slice back-projection — NO 3D padarray (avoids OOM).
% Uses pre-computed z_maps from compute_mip_pictures to
% inverse-map skeleton coords back to 3D.

[H, W, D] = size(V_recon);
cx = (W + 1) / 2;
cz = (D + 1) / 2;

for ai = 1:numel(angles)
    theta  = angles(ai);
    coords = double(skeletons{ai}.coords);  % Nx2 [row, col]
    if isempty(coords), continue; end

    cos_t = cos(deg2rad(theta));
    sin_t = sin(deg2rad(theta));

    DepthMap = z_maps{ai};

    % Back-project skeleton coords using DepthMap
    row_v = coords(:,1);
    col_v = coords(:,2);
    ok    = (row_v >= 1) & (row_v <= H) & (col_v >= 1) & (col_v <= W);
    row_v = row_v(ok);  col_v = col_v(ok);
    if isempty(row_v), continue; end

    lin_idx  = sub2ind([H, W], row_v, col_v);
    z_mip    = double(DepthMap(lin_idx));   % z in original D space

    ok = (z_mip >= 1) & (z_mip <= D);
    row_v = row_v(ok);  col_v = col_v(ok);  z_mip = z_mip(ok);
    if isempty(row_v), continue; end

    % Inverse Y-rotation: recover original X from projected X
    %   X_proj = (X_orig-cx)*cos_t - (z-cz)*sin_t + cx
    %   X_orig = ((X_proj-cx) + (z-cz)*sin_t) / cos_t + cx
    X_proj_rel = col_v - cx;
    Z_rel_v    = z_mip - cz;
    if abs(cos_t) > 1e-6
        X_orig_v = (X_proj_rel + Z_rel_v .* sin_t) ./ cos_t + cx;
    else
        X_orig_v = -Z_rel_v ./ sin_t + cx;
    end
    ox_v = round(X_orig_v);
    ok   = (ox_v >= 1) & (ox_v <= W);
    row_f = round(row_v(ok));  ox_f = round(ox_v(ok));  z_f = round(z_mip(ok));
    if isempty(row_f), continue; end

    lin_recon          = sub2ind(size(V_recon), row_f, ox_f, z_f);
    V_recon(lin_recon) = 1;
end
end


% -------------------------------------------------------------------------
