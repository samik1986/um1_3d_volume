function [skeleton, mip_norm] = compute_skeleton(mip, sigma, min_area, min_branch)
% Extract a 2D vesselness skeleton from a single MIP image.
% Returns skeleton as a STRUCT with coordinate list to save memory:
%   skeleton.coords  - Nx2 single [row, col] of lit skeleton pixels
%   skeleton.H       - image height (rows)
%   skeleton.W       - image width  (cols)
% This avoids storing the full H x W_pad logical array.

[img_H, img_W] = size(mip);
mip = double(mip);
m   = max(mip(:));
if m <= 0
    mip_norm       = single(mip);
    skeleton.coords = zeros(0, 2, 'single');
    skeleton.H      = img_H;
    skeleton.W      = img_W;
    return;
end
mip_norm = single(mip ./ m);

% Light Gaussian smoothing
mip_g = imgaussfilt(double(mip_norm), 1.5);

% Frangi vesselness via MATLAB's fibermetric
try
    vesselness = fibermetric(mip_g, sigma, 'StructureSensitivity', 0.01);
catch ME
    warning('fibermetric failed (%s). Using smoothed MIP directly.', ME.message);
    vesselness = mip_g;
end
vesselness = mat2gray(double(vesselness));

% Adaptive binarisation
BW = imbinarize(vesselness, 'adaptive', ...
     'ForegroundPolarity', 'bright', 'Sensitivity', 0.40);

% Clean boundary artifacts: valid zone is eroded slightly from the original MIP boundaries
valid_mask = mip_norm > 0;
valid_mask = imfill(valid_mask, 'holes');
valid_mask = imerode(valid_mask, strel('disk', 15));
BW(~valid_mask) = false;

BW = bwareaopen(BW, min_area);
BW = imclose(BW, strel('disk', 2));

% Skeletonise
BW_skel = bwskel(logical(BW), 'MinBranchLength', min_branch);

% Store as sparse coordinate list (Nx2 single) — much less RAM than logical array
[r_skel, c_skel] = find(BW_skel);
skeleton.coords  = single([r_skel, c_skel]);   % Nx2, float32
skeleton.H       = img_H;
skeleton.W       = img_W;
end

% -------------------------------------------------------------------------
