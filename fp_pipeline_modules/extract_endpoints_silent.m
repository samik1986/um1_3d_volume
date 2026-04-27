function [pts_start, pts_end] = extract_endpoints_silent(skeletons)
% Extract farthest-pair 2D endpoints from each skeleton (coord-list format).
% Skeleton is struct {coords [Nx2], H, W}.  No find() needed — coords are
% already the row/col pairs, eliminating the dense-array lookup entirely.
% Sub-samples to <= 2000 pts to guard O(N^2) pairwise distance matrix.

num_pics  = numel(skeletons);
pts_start = zeros(num_pics, 2);
pts_end   = zeros(num_pics, 2);
prev_s    = [];  prev_e = [];

for i = 1:num_pics
    coords = double(skeletons{i}.coords);   % Nx2 [row, col]
    % Transpose convention: endpoints expressed as [col, row]
    if size(coords, 1) < 2
        pts_start(i,:) = [NaN, NaN];
        pts_end(i,:)   = [NaN, NaN];
        continue;
    end

    % Re-express as [col, row] to match original convention
    cr = [coords(:,2), coords(:,1)];   % Nx2 [col, row]

    % Subsample to bound O(N^2) pairwise distance
    if size(cr, 1) > 2000
        idx = randperm(size(cr,1), 2000);
        cr = cr(idx, :);
    end

    D2 = (cr(:,1) - cr(:,1)').^2 + (cr(:,2) - cr(:,2)').^2;
    [~, lin] = max(D2(:));
    [iA, iB] = ind2sub(size(D2), lin);
    ptA = cr(iA,:);  ptB = cr(iB,:);

    % Maintain consistent start/end ordering across angles
    if isempty(prev_s)
        if ptA(1) > ptB(1) || (ptA(1)==ptB(1) && ptA(2)>ptB(2))
            [ptA, ptB] = swap_pts(ptA, ptB);
        end
    else
        if norm(ptA-prev_s) + norm(ptB-prev_e) > norm(ptB-prev_s) + norm(ptA-prev_e)
            [ptA, ptB] = swap_pts(ptA, ptB);
        end
    end
    prev_s = ptA;  prev_e = ptB;
    pts_start(i,:) = ptA;
    pts_end(i,:)   = ptB;
end
end

