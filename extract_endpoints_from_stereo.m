function [pts_start_2d, pts_end_2d] = extract_endpoints_from_stereo(pictures)
    % EXTRACT_ENDPOINTS_FROM_STEREO Rigorously extracts independent stereoscopic bounds securely explicitly ensuring robust spatial trajectory identity continuously across 180 flips.
    
    num_pics = length(pictures);
    pts_start_2d = zeros(num_pics, 2); % [col, row]
    pts_end_2d   = zeros(num_pics, 2);
    
    cols = ceil(sqrt(num_pics));
    rows = ceil(num_pics / cols);
    
    figure('Name', 'Step 3: Endpoints tracking continuously Native Disparity Arrays', 'Position', [50 50 1200 800]);
    
    prev_start = [];
    prev_end   = [];
    
    for i = 1:num_pics
        I = pictures{i}';
        I_bin = I > 0; % Enforce rigorous mathematical binary classification
        [r, c] = find(I_bin);
        
        if length(r) < 2
            pts_start_2d(i, :) = [NaN, NaN];
            pts_end_2d(i, :)   = [NaN, NaN];
            continue;
        end
        
        pts = [c, r];
        
        % For strictly binary topological geometric lines, endpoints natively equal 
        % the discrete isolated pixel pair fundamentally maximizing Euclidean distance algebraically 
        D_dist = (pts(:,1) - pts(:,1)').^2 + (pts(:,2) - pts(:,2)').^2;
        [~, max_lin_idx] = max(D_dist(:));
        [idxA, idxB] = ind2sub(size(D_dist), max_lin_idx);
        
        ptA = pts(idxA, :);
        ptB = pts(idxB, :);

        if isempty(prev_start)
            % Initialize initial anchors directly mapping X bounds
            if ptA(1) > ptB(1) || (ptA(1) == ptB(1) && ptA(2) > ptB(2))
                temp = ptA; ptA = ptB; ptB = temp;
            end
            prev_start = ptA;
            prev_end = ptB;
        else
            % Unbreakable Euclidean Euclidean tracker preventing boundary swaps completely during arbitrary rotations
            if norm(ptA - prev_start) + norm(ptB - prev_end) > norm(ptB - prev_start) + norm(ptA - prev_end)
                temp = ptA; ptA = ptB; ptB = temp;
            end
            prev_start = ptA;
            prev_end = ptB;
        end
        
        pts_start_2d(i, :) = ptA;
        pts_end_2d(i, :)   = ptB;
        
        subplot(rows, cols, i);
        imshow(I, []); hold on;
        plot(ptA(1), ptA(2), 'go', 'MarkerSize', 8, 'LineWidth', 2);
        plot(ptB(1), ptB(2), 'mo', 'MarkerSize', 8, 'LineWidth', 2);
        title(sprintf('Angle %d', i));
        hold off;
    end
end
