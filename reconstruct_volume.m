function Reconstructed_V = reconstruct_volume(pictures, angles, ~, volSize)
% RECONSTRUCT_VOLUME Reconstructs a 3D volume using CV Toolbox Stereo Vision
%
% This uses continuous pairs of images (gradual reconstruction across 
% the angle array) connected via disparitySGM. To suppress SGM noise on 
% textureless binary arrays, it implements a 3D voting/accumulation method.

    if nargin < 4 || isempty(volSize)
        [sizeX, sizeY] = size(pictures{1});
        sizeZ = max(sizeX, sizeY); 
        volSize = [sizeX, sizeY, sizeZ];
    end

    if length(pictures) < 2
        error('Stereo vision reconstruction requires at least two pictures to form a stereo pair.');
    end

    % The pictures array is automatically expanded by take_volume_pictures.m to 
    % increase the camera FOV (prevent rotation cropping out boundary structures).
    [pad_sizeX, pad_sizeY] = size(pictures{1});
    pad_sizeZ = pad_sizeX; % Spherical bounding box guarantees padded Z bounds identically match X

    Accum_V = zeros(volSize);
    
    % Imrotate geometrically centers pixels on (N+1)/2 natively
    % Use the true camera plane spatial centroid
    cx_img = (pad_sizeX + 1) / 2;
    cz_img = (pad_sizeZ + 1) / 2;
    
    % Disparity range: SGM needs range that is a multiple of 16.
    dispRange = [-48, 48]; 

    for i = 1:(length(pictures) - 1)
        theta1 = angles(i);
        theta2 = angles(i+1);
        theta_diff = deg2rad(theta2 - theta1);
        
        if abs(sin(theta_diff)) < 1e-4
            continue; % Skip redundant angles
        end
        
        img1 = pictures{i};
        img2 = pictures{i+1};
        
        % Transpose maps 'X' axis to horizontal which is strictly expected by disparitySGM
        I1 = uint8(img1' * 255);
        I2 = uint8(img2' * 255);
        
        try
            D = disparitySGM(I1, I2, 'DisparityRange', dispRange, 'UniquenessThreshold', 0);
        catch
            D = disparityBM(I1, I2, 'DisparityRange', dispRange, 'UniquenessThreshold', 0);
        end
        
        % We reconstruct into the explicitly PADDED volume space to guarantee edge cases aren't
        % chopped off during the inverse-rotation phase!
        Sub_V_padded = zeros(pad_sizeX, pad_sizeY, pad_sizeZ);
        valid_mask = (D > -1000) & (I1 > 128); % Ignore failed BM/SGM matches and background
        
        [R, C] = find(valid_mask);
        
        for k = 1:length(R)
            r = R(k); % Maps directly to original padded Y
            c = C(k); % Maps directly to original padded X in img1
            
            d = D(r, c);
            c2 = c - d; % Maps directly to matching padded X in img2
            
            % Compute distances purely from rotational camera center
            xl_centered = c - cx_img;
            xr_centered = c2 - cx_img;
            
            % Solve exclusively for Z-depth relative to angle theta1
            zl_centered = (xl_centered * cos(theta_diff) - xr_centered) / sin(theta_diff);
            
            % Form structural coordinates mapped safely precisely against PADDED frame
            orig_X = round(c);
            orig_Y = round(r);
            orig_Z = round(zl_centered + cz_img);
            
            if orig_X >= 1 && orig_X <= pad_sizeX && ...
               orig_Y >= 1 && orig_Y <= pad_sizeY && ...
               orig_Z >= 1 && orig_Z <= pad_sizeZ
               
                Sub_V_padded(orig_X, orig_Y, orig_Z) = 1;
            end
        end
        
        % Inverse rotate exactly within the physically PADDED spherical bounding box
        % Using 'nearest' interpolation to preserve binary structural intensity!
        Sub_V_perm = permute(Sub_V_padded, [1, 3, 2]); % [X, Z, Y]
        Sub_V_rot = imrotate(Sub_V_perm, -theta1, 'nearest', 'crop');
        Sub_V_aligned_padded = ipermute(Sub_V_rot, [1, 3, 2]); % [X, Y, Z]
        
        % Crop safely back OUT the true original 100x100 hardware cube bounds seamlessly!
        px = floor((pad_sizeX - volSize(1))/2) + 1;
        py = floor((pad_sizeY - volSize(2))/2) + 1;
        pz = floor((pad_sizeZ - volSize(3))/2) + 1;
        
        Sub_V_aligned = Sub_V_aligned_padded(...
            px : px + volSize(1) - 1, ...
            py : py + volSize(2) - 1, ...
            pz : pz + volSize(3) - 1);
        
        % Increment the accumulator to vote!
        Accum_V = Accum_V + double(Sub_V_aligned > 0);
    end
    
    % --- STRUCTURAL VOTING THRESHOLD ---
    vote_threshold = max(2, round(length(pictures) * 0.1));
    Reconstructed_V = double(Accum_V >= vote_threshold);
end
