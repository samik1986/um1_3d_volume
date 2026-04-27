function visualize_full_cells_subset()
    % VISUALIZE_FULL_CELLS_SUBSET Overlays full cell bodies (3D surfaces) on a volume.
    
    input_file = 'Q4_bottom_right.tif';
    fprintf('Loading volume from %s...\n', input_file);
    
    % Load intensity volume
    info = imfinfo(input_file);
    num_slices = numel(info);
    h = info(1).Height;
    w = info(1).Width;
    V = zeros(h, w, num_slices, 'uint16');
    for z = 1:num_slices
        V(:,:,z) = imread(input_file, z);
    end
    V = single(V);
    
    % Step 1: Detect cells (full mask)
    fprintf('Step 1: Segmenting full cell bodies...\n');
    V_smooth = imgaussfilt3(V, 15);
    thresh = quantile(V_smooth(:), 0.98); 
    L = uint16(bwlabeln(V_smooth > thresh));
    
    % Step 2: 3D Surface Visualization
    fprintf('Step 2: Creating 3D surface overlay...\n');
    figure('Color', 'k', 'Name', 'Full 3D Cell Reconstruction Overlay', 'Position', [100, 100, 1000, 800]);
    hold on;
    
    % 2a. Intensity Volume context (MIP slices as "cages")
    % Show center slices as faint guides
    mid_z = round(num_slices/2);
    [mx, my] = meshgrid(1:w, 1:h);
    slice_img = V(:,:,mid_z);
    surface(mx, my, ones(size(slice_img))*mid_z, slice_img, ...
            'FaceColor', 'texturemap', 'EdgeColor', 'none', 'FaceAlpha', 0.15);
    
    % 2b. Isosurface of full cells
    num_cells = max(L(:));
    cmap = colorcube(double(num_cells + 1));
    
    fprintf('   Generating surfaces for %d cells...\n', num_cells);
    for i = 1:num_cells
        % Only render if cell has some bulk
        if sum(L(:) == i) < 100, continue; end
        
        % Extract cell-specific mask
        cell_mask = (L == i);
        
        % Smooth the mask slightly for a better isosurf
        cell_mask_s = imgaussfilt3(single(cell_mask), 1);
        
        fv = isosurface(cell_mask_s, 0.5);
        if isempty(fv.vertices), continue; end
        
        patch(fv, 'FaceColor', cmap(i+1, :), 'EdgeColor', 'none', ...
              'FaceAlpha', 0.9, 'SpecularStrength', 0.5);
    end
    
    % Step 3: Scene setup
    camlight('headlight');
    lighting gouraud;
    material shiny;
    colormap(gray);
    
    view(3); grid on;
    set(gca, 'Color', 'k', 'XColor', 'w', 'YColor', 'w', 'ZColor', 'w');
    set(gca, 'ZDir', 'reverse');
    xlabel('X'); ylabel('Y'); zlabel('Z');
    title('Full 3D Cell Body Overlay', 'Color', 'w', 'FontSize', 16);
    axis tight; daspect([1 1 1]);
    
    % Save render
    fprintf('Saving result to full_cell_3d_overlay.png...\n');
    exportgraphics(gcf, 'full_cell_3d_overlay.png', 'Resolution', 300);
end
