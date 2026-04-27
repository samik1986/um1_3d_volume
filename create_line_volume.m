function [V, pt1, pt2] = create_line_volume(volSize, pt1, pt2)
    % CREATE_LINE_VOLUME Maps a discrete mathematical line rigidly across a defined 3D matrix.
    % Outputs the binary spatial matrix naturally.
    
    V = zeros(volSize);
    num_points_line = max(abs(pt2 - pt1)) * 2;
    if num_points_line == 0, num_points_line = 1; end
    
    X_line = round(linspace(pt1(1), pt2(1), num_points_line));
    Y_line = round(linspace(pt1(2), pt2(2), num_points_line));
    Z_line = round(linspace(pt1(3), pt2(3), num_points_line));

    for k = 1:length(X_line)
        if X_line(k)>=1 && X_line(k)<=volSize(1) && ...
           Y_line(k)>=1 && Y_line(k)<=volSize(2) && ...
           Z_line(k)>=1 && Z_line(k)<=volSize(3)
            V(X_line(k), Y_line(k), Z_line(k)) = 1;
        end
    end
    
    % Step 1 Figure Artifact Generation
    figure('Name', 'Step 1: Original Line Volume');
    [x, y, z] = ind2sub(volSize, find(V));
    scatter3(x, y, z, 50, 'r', 'filled');
    axis([0 volSize(1) 0 volSize(2) 0 volSize(3)]);
    grid on; box on; view(3); xlabel('X'); ylabel('Y'); zlabel('Z');
    title('Step 1: Original 3D Native Target Line Array');
end
