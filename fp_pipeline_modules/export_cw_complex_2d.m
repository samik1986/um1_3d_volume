function export_cw_complex_2d(graph_data, output_prefix)
    % EXPORT_CW_COMPLEX_2D Exports a biological skeleton graph to a 1D CW Complex in CSV format.
    % 0-cells = vertices.csv
    % 1-cells = edges.csv (bounding 0-cells) and edge_geometry.csv (interior path)
    
    if isempty(graph_data.nodes)
        return; % Nothing to export
    end
    
    % --- 1. Export Vertices (0-Cells) ---
    vert_file = [output_prefix '_cw_vertices.csv'];
    fid = fopen(vert_file, 'w');
    fprintf(fid, 'NodeID,Row_Y,Col_X,Type\n');
    for i = 1:size(graph_data.nodes, 1)
        % type: 1=Endpoint, 3=Junction
        fprintf(fid, '%d,%.2f,%.2f,%d\n', i, graph_data.nodes(i,1), graph_data.nodes(i,2), graph_data.node_type(i));
    end
    fclose(fid);
    
    % --- 2. Export Edges (1-Cells Bounding Map) ---
    edge_file = [output_prefix '_cw_edges.csv'];
    fid = fopen(edge_file, 'w');
    fprintf(fid, 'EdgeID,SourceNodeID,TargetNodeID\n');
    num_edges = size(graph_data.edges, 1);
    for i = 1:num_edges
        fprintf(fid, '%d,%d,%d\n', i, graph_data.edges(i,1), graph_data.edges(i,2));
    end
    fclose(fid);
    
    % --- 3. Export Edge Geometry (1-Cells Interior Path) ---
    % Represents the geometric relationship defining how the 1-cell is routed across space
    geom_file = [output_prefix '_cw_edge_geometry.csv'];
    fid = fopen(geom_file, 'w');
    fprintf(fid, 'EdgeID,SeqIndex,Row_Y,Col_X\n');
    for i = 1:num_edges
        path_coords = graph_data.edge_paths{i};
        for j = 1:size(path_coords, 1)
            fprintf(fid, '%d,%d,%.1f,%.1f\n', i, j, path_coords(j,1), path_coords(j,2));
        end
    end
    fclose(fid);
    
end
