function V = create_point_volume(volSize, pt)
    % CREATE_POINT_VOLUME Initializes a localized 3D matrix tracking a discrete point coordinate
    %
    % V = create_point_volume(volSize, pt)
    
    V = zeros(volSize);
    if pt(1) >= 1 && pt(1) <= volSize(1) && ...
       pt(2) >= 1 && pt(2) <= volSize(2) && ...
       pt(3) >= 1 && pt(3) <= volSize(3)
        V(pt(1), pt(2), pt(3)) = 1;
    else
        warning('Initial point is entirely out of bounds.');
    end
end
