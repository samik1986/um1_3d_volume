function plot_cw_complex(cw_json)
    % PLOT_CW_COMPLEX Evaluates arrays strictly from the native JSON rendering physical sequences explicitly ignoring topological toolboxes.
    
    figure('Color', 'k', 'Name', '1D CW Complex Visualiser'); hold on;
    axis equal; set(gca, 'Color', 'k', 'XColor', 'w', 'YColor', 'w');
    title('Mathematical 1D JSON Physical Trace', 'Color', 'w');
    
    % Draw true geometric physical splines explicitly tracing arrays
    if isfield(cw_json, 'cells_1_linestrings') && ~isempty(cw_json.cells_1_linestrings)
        lines = cw_json.cells_1_linestrings;
        for i = 1:length(lines)
            geom = lines(i).geometry;
            if size(geom, 2) == 1 && size(geom, 1) == 2
                geom = geom'; % MATLAB jsondecode transposes single 1x2 points to 2x1 natively
            end
            if size(geom, 1) >= 3
                % Parametric curve smoothing to eliminate discretization zigzags
                t = [0; cumsum(sqrt(sum(diff(geom).^2, 2)))]; 
                [t_unique, idx_unique] = unique(t);
                
                if length(t_unique) >= 3
                    t_query = linspace(0, t_unique(end), max(100, length(t_unique)*4));
                    % Use pchip to prevent severe overshoots on tight topological corners
                    x_smooth = pchip(t_unique, geom(idx_unique, 2), t_query);
                    y_smooth = pchip(t_unique, geom(idx_unique, 1), t_query);
                    plot(x_smooth, y_smooth, 'w-', 'LineWidth', 1.5);
                else
                    plot(geom(:, 2), geom(:, 1), 'w-', 'LineWidth', 1.5);
                end
            else
                plot(geom(:, 2), geom(:, 1), 'w-', 'LineWidth', 1.5);
            end
        end
    end
    
    % Overlap 0-cell explicitly defined bounding classes
    if isfield(cw_json, 'cells_0_nodes') && ~isempty(cw_json.cells_0_nodes)
        nodes = cw_json.cells_0_nodes;
        for i = 1:length(nodes)
            x = nodes(i).coord(2);
            y = nodes(i).coord(1);
            t = nodes(i).type;
            
            if strcmp(t, 'boundary')
                plot(x, y, '^r', 'MarkerSize', 6, 'MarkerFaceColor', 'r');
            else
                plot(x, y, 'ob', 'MarkerSize', 5, 'MarkerFaceColor', 'b');
            end
        end
    end
    
    % Legend rendering natively configured correctly
    h1 = plot(NaN, NaN, '^r', 'MarkerFaceColor', 'r');
    h2 = plot(NaN, NaN, 'ob', 'MarkerFaceColor', 'b');
    h3 = plot(NaN, NaN, 'w-', 'LineWidth', 1.5);
    legend([h1, h2, h3], {'Boundary (Endpoints)', 'Junctions (Trees)', 'Linestrings'}, 'TextColor', 'w', 'Color', 'none');
    
    view(2); hold off;
end
