function export_cw_complex_json(graph_data, prefix)
    % EXPORT_CW_COMPLEX_JSON Exports the 2D skeleton graph into a strict 1D CW-Complex JSON definition.
    % Mapped directly from structural arrays into a consolidated GeoJSON-like features list.
    
    cw = struct();
    cw.network_type = '1D CW Complex Forest';
    
    if isempty(graph_data) || isempty(graph_data.nodes)
        cw.cells_0_nodes = [];
        cw.cells_1_linestrings = [];
        json_str = jsonencode(cw);
        fid = fopen([prefix '_cw_complex.json'], 'w');
        if fid > 0, fwrite(fid, json_str, 'char'); fclose(fid); end
        return;
    end
    
    % --- Feature 1: The 0-Cells (Endpoints and Junctions) ---
    num_nodes = size(graph_data.nodes, 1);
    nodes_array = cell(1, num_nodes);
    
    for i = 1:num_nodes
        if graph_data.node_type(i) == 1
            typ = 'boundary';
        else
            typ = 'junction';
        end
        % Ensure MATLAB doesn't truncate data randomly; explicitly format round coordinates
        coord = round(double(graph_data.nodes(i, :)));
        nodes_array{i} = struct('node_id', i, 'type', typ, 'coord', coord);
    end
    cw.cells_0_nodes = nodes_array;
    
    % --- Feature 2, 3, 4: The 1-Cells (Linestrings / Edge Geometry) ---
    num_edges = size(graph_data.edges, 1);
    edges_array = cell(1, num_edges);
    
    for i = 1:num_edges
        src = graph_data.edges(i, 1);
        tgt = graph_data.edges(i, 2);
        
        path_geom = double(graph_data.edge_paths{i});
        
        % Fetch relationship bounds
        if graph_data.node_type(src) == 1
            src_t = 'boundary';
        else
            src_t = 'junction';
        end
        
        if graph_data.node_type(tgt) == 1
            tgt_t = 'boundary';
        else
            tgt_t = 'junction';
        end
        
        % Consolidate into structural features cleanly mapped
        edges_array{i} = struct( ...
            'line_id', i, ...
            'endpoints', struct('source_id', src, 'target_id', tgt), ...
            'geometry', path_geom, ...
            'forest_relation', struct('connects', {{src_t, tgt_t}}) ...
        );
    end
    cw.cells_1_linestrings = edges_array;
    
    % Export cleanly
    try
        % Use PrettyPrint if MATLAB natively supports it (R2021a+)
        json_str = jsonencode(cw, 'PrettyPrint', true);
    catch
        json_str = jsonencode(cw);
    end
    
    fid = fopen([prefix '_cw_complex.json'], 'w');
    if fid > 0
        fwrite(fid, json_str, 'char');
        fclose(fid);
        fprintf('   -> Exported JSON CW Complex: %s_cw_complex.json\n', prefix);
    else
        warning('Failed to open output json file for %s', prefix);
    end
end
