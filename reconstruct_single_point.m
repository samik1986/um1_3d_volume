function Reconstructed_V = reconstruct_single_point(pictures, angles, volSize)
    % RECONSTRUCT_SINGLE_POINT Generates volumetric depth mapping bounds explicitly structured for point resolution
    %
    % Reconstructed_V = reconstruct_single_point(pictures, angles, volSize)

    [pad_sizeY, pad_sizeX] = size(pictures{1}');
    pad_sizeZ = pad_sizeX; 

    cx_img = (pad_sizeX + 1) / 2;
    cy_img = (pad_sizeY + 1) / 2;
    cz_img = (pad_sizeZ + 1) / 2;

    Accum_V = zeros(volSize);
    valid_pairs = 0;

    for i = 1:(length(angles) - 1)
        theta1 = angles(i);
        theta2 = angles(i+1);
        theta_diff = deg2rad(theta2 - theta1);
        
        if abs(sin(theta_diff)) < 1e-4
            continue;
        end
        
        I1 = pictures{i}';
        I2 = pictures{i+1}';
        
        [max_val1, max_idx1] = max(I1(:));
        [r1, c1] = ind2sub(size(I1), max_idx1);
        
        [max_val2, max_idx2] = max(I2(:));
        [r2, c2] = ind2sub(size(I2), max_idx2);
        
        if max_val1 > 0.1 && max_val2 > 0.1
            valid_pairs = valid_pairs + 1;
            
            xl_centered = c1 - cx_img;
            xr_centered = c2 - cx_img;
            
            zl_centered = (xl_centered * cos(theta_diff) - xr_centered) / sin(theta_diff);
            
            orig_X = round(c1);
            orig_Y = round(r1); 
            orig_Z = round(zl_centered + cz_img);
            
            Sub_V_padded = zeros(pad_sizeX, pad_sizeY, pad_sizeZ);
            
            if orig_X >= 1 && orig_X <= pad_sizeX && ...
               orig_Y >= 1 && orig_Y <= pad_sizeY && ...
               orig_Z >= 1 && orig_Z <= pad_sizeZ
               
                Sub_V_padded(orig_X, orig_Y, orig_Z) = 1;
            end
            
            Sub_V_perm = permute(Sub_V_padded, [1, 3, 2]); 
            Sub_V_rot = imrotate(Sub_V_perm, -theta1, 'nearest', 'crop');
            Sub_V_aligned_padded = ipermute(Sub_V_rot, [1, 3, 2]); 
            
            px = floor((pad_sizeX - volSize(1))/2) + 1;
            py = floor((pad_sizeY - volSize(2))/2) + 1;
            pz = floor((pad_sizeZ - volSize(3))/2) + 1;
            
            Sub_V_aligned = Sub_V_aligned_padded(...
                px : px + volSize(1) - 1, ...
                py : py + volSize(2) - 1, ...
                pz : pz + volSize(3) - 1);
                
            Accum_V = Accum_V + double(Sub_V_aligned > 0);
        end
    end

    % Dynamically bind threshold strictly accommodating low stereo-pair evaluations (e.g. single pairs!)
    vote_threshold = max(1, round(valid_pairs * 0.15));
    if valid_pairs >= 10, vote_threshold = max(3, vote_threshold); end
    
    Reconstructed_V = Accum_V >= vote_threshold;
end
