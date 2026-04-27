function test_single_point_stereo(test_points)
% TEST_SINGLE_POINT_STEREO Runs modular stereo gradual reconstruction on a dynamic set of points.
%
% USAGE:
%   test_single_point_stereo(test_points)
%
% INPUT:
%   test_points : Nx3 array of [X, Y, Z] spatial input coordinates

    if nargin < 1 || isempty(test_points)
        % Default robust validation set if no external dynamic input is provided
        test_points = [
            70, 50, 30;  
            10, 90, 10;  
            90, 90, 90;  
            1, 1, 1;     
            100, 100, 100;
        ];
    end

    %% 1. Configuration Setup
    volSize = [100, 100, 100];
    angles = 0:10:180; % Continuous sweeping angles

    fprintf('=== MODULAR STEREO RECONSTRUCTION INPUT PIPELINE ===\n\n');

% Initialize unified graphical frame (Step 4 setup)
fig_overlay = figure('Name', 'Modular Stereo Validation Overlay', 'Position', [100, 100, 800, 800]);
hold on; grid on; box on; view(3);
axis([0 volSize(1) 0 volSize(2) 0 volSize(3)]);
xlabel('X (Row)'); ylabel('Y (Col)'); zlabel('Z (Depth)');
title('Modular Pipeline Overlay: Target (Red) vs Reconstructed (Blue)');

h_orig = [];
h_recon = [];

%% --- PIPELINE EXECUTION ---
for pt_idx = 1:size(test_points, 1)
    orig_point = test_points(pt_idx, :);
    fprintf('\n--- Point %d: (%d, %d, %d) ---\n', pt_idx, orig_point(1), orig_point(2), orig_point(3));
    
    % Step 1: Create a volume with a point
    V = create_point_volume(volSize, orig_point);
    
    % Step 2: Take the volume to create stereo vision images at different camera angles 
    pictures = take_volume_pictures(V, angles, 'Y');
    
    % Step 3: Take these images and reconstruct back the 3D point
    Reconstructed_V = reconstruct_single_point(pictures, angles, volSize);
    
    % Step 4: Add visualization of the original and reconstructed point overlayed
    figure(fig_overlay); % Strictly lock plotting focus correctly back to the segregated 3D Overlay Window
    [ho, hr] = add_overlay_visualization(V, Reconstructed_V, volSize);
    
    if isempty(h_orig) && ~isempty(ho), h_orig = ho; end
    if isempty(h_recon) && ~isempty(hr), h_recon = hr; end
end

hold off;

    saveas(fig_overlay, 'C:\Users\banerjee\.gemini\antigravity\brain\30d2e639-d822-4229-abed-ca661719e24d\qa_points_overlay.png');
    disp('Execution Complete. Overlay visualization saved.');

end % End of MAIN Function Wrapper


%% --- MODULAR PIPELINE LOCAL FUNCTIONS ---

function V = create_point_volume(volSize, pt)
    % Step 1. Creates an empty 3D volume and defines a distinct point location
    V = zeros(volSize);
    if pt(1) >= 1 && pt(1) <= volSize(1) && ...
       pt(2) >= 1 && pt(2) <= volSize(2) && ...
       pt(3) >= 1 && pt(3) <= volSize(3)
        V(pt(1), pt(2), pt(3)) = 1;
    else
        warning('Initial point is entirely out of bounds.');
    end
end

function Reconstructed_V = reconstruct_single_point(pictures, angles, volSize)
    % Step 3. Calculates exact spatial disparity shifts perfectly mapped strictly for precise points
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

    vote_threshold = max(3, round(valid_pairs * 0.15));
    Reconstructed_V = Accum_V >= vote_threshold;
end

function [h_orig, h_recon] = add_overlay_visualization(V_orig, V_recon, volSize)
    % Step 4. Plotly accurately stacks Original and Reconstructed spatial traces 
    h_orig = [];
    h_recon = [];

    [x_orig, y_orig, z_orig] = ind2sub(volSize, find(V_orig));
    if ~isempty(x_orig)
        h_orig = scatter3(x_orig, y_orig, z_orig, 300, 'r', 'filled', 'MarkerFaceAlpha', 0.5);
    end

    [x_recon, y_recon, z_recon] = ind2sub(volSize, find(V_recon));
    if ~isempty(x_recon)
        h_recon = scatter3(x_recon, y_recon, z_recon, 50, 'b', 'filled');
        mean_X = round(mean(x_recon));
        mean_Y = round(mean(y_recon));
        mean_Z = round(mean(z_recon));
        fprintf('  Reconstructed: (%3.0f, %3.0f, %3.0f)  |  Stable Voxels: %d\n', mean_X, mean_Y, mean_Z, length(x_recon));
        
        orig_centroid = [mean(x_orig), mean(y_orig), mean(z_orig)];
        err = norm(orig_centroid - [mean_X, mean_Y, mean_Z]);
        fprintf('  Absolute Geometric Vector Error: %.2f pixels\n', err);
    else
        fprintf('  FAILED: 0 reconstructed voxels cleared overlap thresholds.\n');
    end
end
