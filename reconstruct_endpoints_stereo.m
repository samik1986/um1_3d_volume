function [recon_pt1, recon_pt2] = reconstruct_endpoints_stereo(pts_start_2d, pts_end_2d, angles, volSize, pic_size)
    % RECONSTRUCT_ENDPOINTS_STEREO Unifies mathematical depth resolution sequentially 
    % overlapping topological intersection clusters accumulating explicitly bounded structures natively.
    
    pad_sizeX = pic_size(2);
    pad_sizeY = pic_size(1);
    pad_sizeZ = pad_sizeX;
    
    cx_img = (pad_sizeX + 1) / 2;
    cy_img = (pad_sizeY + 1) / 2;
    cz_img = (pad_sizeZ + 1) / 2;
    
    px = floor((pad_sizeX - volSize(1))/2) + 1;
    py = floor((pad_sizeY - volSize(2))/2) + 1;
    pz = floor((pad_sizeZ - volSize(3))/2) + 1;

    Accum_V_start = zeros(volSize);
    Accum_V_end   = zeros(volSize);
    valid_pairs   = 0;

    for i = 1:(length(angles) - 1)
        theta1 = angles(i);
        theta2 = angles(i+1);
        theta_diff = deg2rad(theta2 - theta1);
        
        if abs(sin(theta_diff)) < 1e-4
            continue;
        end
        
        c1_s = pts_start_2d(i, 1);   r1_s = pts_start_2d(i, 2);
        c2_s = pts_start_2d(i+1, 1); 
        
        c1_e = pts_end_2d(i, 1);     r1_e = pts_end_2d(i, 2);
        c2_e = pts_end_2d(i+1, 1);   
        
        if isnan(c1_s) || isnan(c2_s) || isnan(c1_e) || isnan(c2_e)
            continue;
        end
        
        valid_pairs = valid_pairs + 1;
        
        % Start point exact stereoscopic depth accumulation
        xl_s = c1_s - cx_img; xr_s = c2_s - cx_img;
        zl_s = (xl_s * cos(theta_diff) - xr_s) / sin(theta_diff);
        ox_s = round(c1_s); oy_s = round(r1_s); oz_s = round(zl_s + cz_img);
        
        Sub_V_padded = zeros(pad_sizeX, pad_sizeY, pad_sizeZ);
        if ox_s>=1 && ox_s<=pad_sizeX && oy_s>=1 && oy_s<=pad_sizeY && oz_s>=1 && oz_s<=pad_sizeZ
            Sub_V_padded(ox_s, oy_s, oz_s) = 1;
        end
        Sub_V_perm = permute(Sub_V_padded, [1, 3, 2]); 
        Sub_V_rot = imrotate(Sub_V_perm, -theta1, 'nearest', 'crop');
        Sub_V_aligned_padded = ipermute(Sub_V_rot, [1, 3, 2]); 
        
        Sub_V_aligned = Sub_V_aligned_padded(px:px+volSize(1)-1, py:py+volSize(2)-1, pz:pz+volSize(3)-1);
        Accum_V_start = Accum_V_start + double(Sub_V_aligned > 0);
        
        % End point exact stereoscopic depth accumulation
        xl_e = c1_e - cx_img; xr_e = c2_e - cx_img;
        zl_e = (xl_e * cos(theta_diff) - xr_e) / sin(theta_diff);
        Sub_V_padded = zeros(pad_sizeX, pad_sizeY, pad_sizeZ);
        ox_e = round(c1_e); oy_e = round(r1_e); oz_e = round(zl_e + cz_img);
        
        if ox_e>=1 && ox_e<=pad_sizeX && oy_e>=1 && oy_e<=pad_sizeY && oz_e>=1 && oz_e<=pad_sizeZ
            Sub_V_padded(ox_e, oy_e, oz_e) = 1;
        end
        Sub_V_perm = permute(Sub_V_padded, [1, 3, 2]); 
        Sub_V_rot = imrotate(Sub_V_perm, -theta1, 'nearest', 'crop');
        Sub_V_aligned_padded = ipermute(Sub_V_rot, [1, 3, 2]); 
        
        Sub_V_aligned = Sub_V_aligned_padded(px:px+volSize(1)-1, py:py+volSize(2)-1, pz:pz+volSize(3)-1);
        Accum_V_end = Accum_V_end + double(Sub_V_aligned > 0);
    end
    
    % Inherently tolerate structural rasterization endpoint discretization jitter 
    % completely spanning complex angle sweeps natively smoothly mapping clusters.
    vote_threshold = 1;
    
    [xs, ys, zs] = ind2sub(volSize, find(Accum_V_start >= vote_threshold));
    [xe, ye, ze] = ind2sub(volSize, find(Accum_V_end   >= vote_threshold));
    
    if isempty(xs), recon_pt1 = [NaN, NaN, NaN]; else, recon_pt1 = [round(mean(xs)), round(mean(ys)), round(mean(zs))]; end
    if isempty(xe), recon_pt2 = [NaN, NaN, NaN]; else, recon_pt2 = [round(mean(xe)), round(mean(ye)), round(mean(ze))]; end

    % Step 4 Figure Artifact Generation
    figure('Name', 'Step 4: Reconstructed Endpoints in 3D');
    if ~isnan(recon_pt1(1)), scatter3(recon_pt1(1), recon_pt1(2), recon_pt1(3), 200, 'g', 'filled'); hold on; end
    if ~isnan(recon_pt2(1)), scatter3(recon_pt2(1), recon_pt2(2), recon_pt2(3), 200, 'm', 'filled'); end
    axis([0 volSize(1) 0 volSize(2) 0 volSize(3)]);
    grid on; box on; view(3); xlabel('X'); ylabel('Y'); zlabel('Z');
    title('Step 4: Gradually Reconstructed Unified Output Clusters');
    hold off;
end
