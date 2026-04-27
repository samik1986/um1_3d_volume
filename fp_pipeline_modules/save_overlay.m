function save_overlay(mip_norm, skeleton, div_idx, angle_val, out_dir)
% Save MIP (JPEG), binary skeleton (PNG), and magenta overlay (JPEG).
% skeleton is a struct {coords, H, W} — reconstruct dense only for imwrite.
prefix = sprintf('SubVol%d_Angle%03d', div_idx, round(angle_val));
mip_d  = double(mip_norm);                        % double required by imoverlay

% Reconstruct dense logical from coordinate list (temporary, local only)
BW_dense = false(skeleton.H, skeleton.W);
if ~isempty(skeleton.coords)
    lin = sub2ind([skeleton.H, skeleton.W], ...
                  double(skeleton.coords(:,1)), double(skeleton.coords(:,2)));
    BW_dense(lin) = true;
end

imwrite(uint8(mip_d .* 255), fullfile(out_dir, [prefix '_MIP.jpg']));
imwrite(BW_dense,             fullfile(out_dir, [prefix '_Skeleton.png']));
ovr = imoverlay(mip_d, BW_dense, [1, 0, 1]);      % magenta overlay
imwrite(ovr,                  fullfile(out_dir, [prefix '_Overlay.jpg']));
end

% -------------------------------------------------------------------------
