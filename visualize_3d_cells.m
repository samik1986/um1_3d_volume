function visualize_3d_cells()
    % VISUALIZE_3D_CELLS Creates a premium 3D visualization of detected cells.
    
    % Load results
    if ~exist('cell_detections_subset.mat', 'file')
        error('Detections not found. Please run detect_3d_cells_blob first.');
    end
    load('cell_detections_subset.mat', 'centroids', 'stats');
    
    % Load subset volume for context
    input_file = 'Q4_bottom_right.tif';
    info = imfinfo(input_file);
    num_slices = numel(info);
    h = info(1).Height;
    w = info(1).Width;
    V = zeros(h, w, num_slices, 'uint16');
    for z = 1:num_slices
        V(:,:,z) = imread(input_file, z);
    end
    
    figure('Color', [0.1, 0.1, 0.1], 'Name', '3D Cell Body Visualizer', 'Position', [100, 100, 1000, 800]);
    hold on;
    
    % Step 1: Draw a semi-transparent volume context (MIP or Isosurface)
    % We'll use a Maximum Intensity Projection as a floor and a sparse 
    % point cloud for volume context to keep it snappy.
    fprintf('Rendering 3D scene...\n');
    
    % Draw "Cell Spheres"
    % Normalize volumes for sizing
    vols = stats.Volume;
    if ~isempty(vols)
        sizes = 100 * (vols / max(vols)) + 50; % Scale sphere sizes
    else
        sizes = 100;
    end
    
    % Use a nice colormap for intensity
    cmap = winter(size(centroids, 1));
    
    % Draw each cell as a 3D sphere
    [sx, sy, sz] = sphere(20);
    radius_base = 10; % pixels
    
    for i = 1:size(centroids, 1)
        r = radius_base * (vols(i)/mean(vols))^0.33; % Volume-based radius
        surf(sx*r + centroids(i,1), ...
             sy*r + centroids(i,2), ...
             sz*r + centroids(i,3), ...
             'EdgeColor', 'none', 'FaceColor', cmap(i,:), 'FaceAlpha', 0.8);
    end
    
    % Context: Bottom plane MIP
    mip = max(V, [], 3);
    [mx, my] = meshgrid(1:w, 1:h);
    surface(mx, my, ones(size(mip)) * (num_slices + 10), mip, ...
            'FaceColor', 'texturemap', 'EdgeColor', 'none', 'FaceAlpha', 0.4);
    colormap(winter);
    
    % Lighting and Camera
    camlight('headlight');
    camlight('right');
    lighting gouraud;
    material shiny;
    
    % Aesthetics
    view(3);
    grid on;
    set(gca, 'Color', [0.1, 0.1, 0.1], 'XColor', 'w', 'YColor', 'w', 'ZColor', 'w');
    set(gca, 'ZDir', 'reverse');
    xlabel('X (pixels)'); ylabel('Y (pixels)'); zlabel('Depth (slices)');
    title('3D Biological Cell Reconstruction', 'Color', 'w', 'FontSize', 16);
    
    axis tight;
    daspect([1 1 1]); % Equal aspect ratio
    
    % Save high-res output
    fprintf('Saving high-resolution render...\n');
    exportgraphics(gcf, 'cell_3d_render.png', 'Resolution', 300);
end
