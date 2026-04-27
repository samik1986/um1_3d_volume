
V = tiffreadVolume('B1Well5_w1s2l__640_F0065.tif');
FP = tiffreadVolume("FP.tif");
% Define your spacing (e.g., voxels are 0.5 x 0.5 x 2.0 units)
sx = 0.1102; sy = 0.1102; sz = 0.5;

A = [sx 0 0 0; 0 sy 0 0; 0 0 sz 0; 0 0 0 1];
tform = affinetform3d(A); 

h = volshow(V, 'Transformation', tform, ...
    'RenderingStyle', 'Isosurface');
h.IsosurfaceValue = 0.016;


volumeViewer(V)

%% MIP
mip = max(V, [], 3);
figure; imshow(mip, [0 500]); title('Maximum Intensity Projection');
imwrite(mip, 'MIP_F65.jp2');

BW = mip>400;

BWm = imgaussfilt(double(BW), 11);
skel = bwskel(BWm > 0.01);
se = strel("disk",3);
skelT = imdilate(skel, se);
ovr = imoverlay(uint8(mip/2), skelT, 'g');
mipD = im2double(mip);

mipN = mip;
mipN(mipN>500) = 500;
mipN = mat2gray(mipN);

%%
vNess = FrangiFilter2D(mipN); %, ...
    % 'FrangiScaleRange', [1 10], ...
    % 'FrangiScaleRatio', 2, ...
    % 'FrangiBetaOne', 0.5, ...
    % 'FrangiBetaTwo', 15, ....
    % 'verbose',true, ...
    % 'BlackWhite',true);

vNessN = mat2gray(vNess);
vNessI = imcomplement(vNessN);


V = fibermetric(mipN, 'Thickness', [5 5]); 
BW = V > 0.1;
Skel = bwskel(BW, 'MinBranchLength', 15);
Skel = bwareaopen(Skel, 50);
Skel = imdilate(Skel, se);
% Skel = bwmorph(Skel, "thicken", 2);
lblN = labeloverlay(mipN, Skel, 'Transparency', 0);
imshow(lblN);


%%
meanIP = mean(V, 3);

% 3. Display result

figure; imshow(meanIP, []); title('Average Intensity Projection');
%% 
filename = 'B1Well5_w1s2l__640_F0065.tif';
info = imfinfo(filename);
num_slices = numel(info);
width = info(1).Width;
height = info(1).Height;

% Preallocate 3D array for speed
vol = zeros(height, width, num_slices, 'single'); 

for k = 1:num_slices
    vol(:,:,k) = imread(filename, k);
end

%% 2. Normalize or Scale Data (Optional)
% If your 0.01 value is on a 0-1 scale, but the TIFF is 8-bit:
vol = mat2gray(vol); 

%% 3. Generate the Isosurface
isoValue = 0.01;
figure('Color', 'w');

% Create the isosurface mesh
% Note: isosurface(V) uses pixel coordinates. 
% For physical units, use isosurface(X, Y, Z, V, isoValue)
fv = isosurface(vol, isoValue);

% Calculate normals for smooth lighting
nm = isonormals(vol, fv.vertices);

%% 4. Render the Projection
p = patch(fv);
set(p, 'FaceColor', [0.7, 0.2, 0.2], ... % Dark Red
       'EdgeColor', 'none', ...
       'FaceAlpha', 1);

% Add caps if the surface is cut off at the volume boundaries
patch(isocaps(vol, isoValue), 'FaceColor', 'interp', 'EdgeColor', 'none');

%% 5. Visualization Settings
view(3);                    % 3D View
axis tight; axis equal;     % Maintain aspect ratio
camlight;                   % Add light source
lighting gouraud;           % Smooth shading
grid on;
title(['Projection of TIFF Volume at ', num2str(isoValue)]);


