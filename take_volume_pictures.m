function pictures = take_volume_pictures(V, angles, rotation_axis)
% TAKE_VOLUME_PICTURES Takes 2D pictures of a 3D volume at different angles.
% The camera is positioned perpendicular to the XY plane (projecting along the Z-axis).
% The volume is rotated at the specified angles before taking the projection.
%
% Inputs:
%   V             - 3D matrix representing the volume (indexed as V(x, y, z))
%   angles        - Array of angles (in degrees) to rotate
%   rotation_axis - (Optional) Axis to rotate the volume around: 'X', 'Y', or 'Z'. 
%                   Defaults to 'Y'. 
%
% Output:
%   pictures      - Cell array containing 2D images (Maximum Intensity Projections)

    if nargin < 3
        rotation_axis = 'Y';
    end

    % INCREASE CAMERA FIELD OF VIEW (FOV)
    % We expand the 3D volume symmetrically into a spherical bounding box to 
    % ensure the camera field of view easily captures all edge cases during rotation.
    [X, Y, Z] = size(V);
    switch upper(rotation_axis)
        case 'Y'
            max_dim = ceil(sqrt(X^2 + Z^2));
            pad_X = max_dim - X; pad_Z = max_dim - Z; pad_Y = 0;
        case 'X'
            max_dim = ceil(sqrt(Y^2 + Z^2));
            pad_Y = max_dim - Y; pad_Z = max_dim - Z; pad_X = 0;
        case 'Z'
            max_dim = ceil(sqrt(X^2 + Y^2));
            pad_X = max_dim - X; pad_Y = max_dim - Y; pad_Z = 0;
        otherwise
            pad_X = 0; pad_Y = 0; pad_Z = 0;
    end
    
    pad_pre = [floor(pad_X/2), floor(pad_Y/2), floor(pad_Z/2)];
    pad_post = [ceil(pad_X/2), ceil(pad_Y/2), ceil(pad_Z/2)];
    
    V_padded = padarray(V, pad_pre, 0, 'pre');
    V_padded = padarray(V_padded, pad_post, 0, 'post');

    num_angles = length(angles);
    pictures = cell(1, num_angles);
    
    % Prepare subplot figure
    figure('Name', 'Volume Projections');
    cols = ceil(sqrt(num_angles));
    rows = ceil(num_angles / cols);

    for idx = 1:num_angles
        theta = angles(idx);
        
        % Rotate the volume based on the specified axis
        % Assumes MATLAB dimensions 1, 2, 3 correspond to X, Y, Z axes
        switch upper(rotation_axis)
            case 'Z'
                % Rotate the X-Y plane (Dimensions 1 and 2)
                V_rot = imrotate(V_padded, theta, 'bilinear', 'crop');
                
            case 'Y'
                % Rotate the X-Z plane.
                V_perm = permute(V_padded, [1, 3, 2]);
                V_rot_perm = imrotate(V_perm, theta, 'bilinear', 'crop');
                V_rot = ipermute(V_rot_perm, [1, 3, 2]);
                
            case 'X'
                % Rotate the Y-Z plane. 
                V_perm = permute(V_padded, [2, 3, 1]);
                V_rot_perm = imrotate(V_perm, theta, 'bilinear', 'crop');
                V_rot = ipermute(V_rot_perm, [2, 3, 1]);

                
            otherwise
                error('Invalid rotation_axis. Please use ''X'', ''Y'', or ''Z''.');
        end
        
        % Take the picture perpendicular to the XY plane (project along the Z-axis)
        % We use max(..., [], 3) to get the Maximum Intensity Projection (MIP)
        % This flattens the 3rd dimension (Z) onto the 1st and 2nd dimensions (X, Y)
        pic = max(V_rot, [], 3);
        
        pictures{idx} = pic;
        
        % Display the picture in a subplot
        subplot(rows, cols, idx);
        imshow(pic, []);
        title(sprintf('%d\\circ (%s-axis)', theta, upper(rotation_axis)));
    end
end
