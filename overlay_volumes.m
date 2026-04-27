% overlay_volumes.m
% Script to overlay FP.tiff (original volume) with the reconstructed skeleton volume
% Both arrays are converted into a uint8 memory mapping and displayed interactively.

clear; clc; close all;

% Define file paths (modify these if your filenames differ slightly)
orig_file = 'FP.tif'; 
if ~isfile(orig_file)
    orig_file = 'FP.tiff'; % Check alternate extension
end

% Look for the MATLAB generated skeleton or the C++ generated one
recon_file = fullfile('fp_pipeline_output', 'FP_reconstructed_skeleton.tif');
if ~isfile(recon_file)
    recon_file = 'FP_reconstructed_cpp.tif'; % Fallback to C++ output
end

if ~isfile(orig_file)
    error('Original volume file not found. Ensure FP.tif or FP.tiff is in the directory.');
end
if ~isfile(recon_file)
    error('Reconstructed skeleton file not found.');
end

disp(['Loading Original Volume: ', orig_file]);
info_orig = imfinfo(orig_file);
num_slices = numel(info_orig);
H = info_orig(1).Height;
W = info_orig(1).Width;

% Pre-allocate memory for speed
V_orig = zeros(H, W, num_slices, 'uint8');
V_recon = false(H, W, num_slices);

disp('Reading slices and converting to uint8...');
for z = 1:num_slices
    % 1. Read original slice
    sl = imread(orig_file, z);
    
    % Convert FP (often 16-bit or variable) to uint8 rigorously
    if isa(sl, 'uint16')
        % Standard mapping (divide by theoretical 16-bit max)
        % If your signals are faint, mat2gray(sl) might be preferred before uint8 scaling
        sl = uint8( (double(sl) ./ 65535.0) .* 255.0 );
    elseif isa(sl, 'single') || isa(sl, 'double')
        sl = uint8(sl .* 255.0);
    elseif isa(sl, 'logical')
        sl = uint8(sl) .* 255;
    else
        sl = uint8(sl);
    end
    V_orig(:,:,z) = sl;
    
    % 2. Read skeleton slice
    sr = imread(recon_file, z);
    V_recon(:,:,z) = (sr > 0); % Store purely as logical threshold
end
disp('Volumes loaded successfully into memory.');

%% Visualization 1: Maximum Intensity Projection (MIP) 2D Overlay
disp('Generating MIP Overlay...');
mip_orig = max(V_orig, [], 3);
mip_recon = max(V_recon, [], 3);

% Colorize the skeleton as pure RED superimposed on the greyscale original
rgb_mip = cat(3, max(mip_orig, uint8(mip_recon)*255), mip_orig, mip_orig);

figure('Name', 'Maximum Intensity Projection (MIP) Overlay', 'NumberTitle', 'off');
imshow(rgb_mip);
title('MIP Z-Projection: Skeletons shown in Red');

%% Visualization 2: 3D Render & Interactive Slice Viewer
disp('Launching Interactive Viewers...');

try
    % Modern MATLAB (2022a+) Image Processing Toolbox feature
    % sliceViewer provides a highly efficient anatomical scroll UI 
    sliceViewer(V_orig, 'OverlayData', V_recon);
    disp('sliceViewer launched successfully.');
catch
    disp('sliceViewer not fully supported. Falling back to simple 3D volshow...');
end

try
    % Render a fully interactive 3D volumetric raycast
    figure('Name', 'Fully 3D Render', 'NumberTitle', 'off');
    h = volshow(V_orig);
    h.OverlayData = V_recon;          % Inject the skeleton mask
    h.OverlayAlphamap = 0.4;          % Make skeleton highly opaque
    h.OverlayColormap = [1, 0, 0];    % Solid Red
    disp('Completed 3D volshow rendering.');
catch
    disp('Advanced volume overlay requires newer Medical/Image toolboxes.');
end

disp('Done!');
