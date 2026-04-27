function export_forest_to_json(G, out_path)
    % EXPORT_FOREST_TO_JSON Reversions the edited natively bounded graph objects back into serialized CW JSON strings dynamically saving modifications.
    
    cw = struct();
    cw.network_type = '1D CW Complex Forest (Edited)';
    
    % Serialize Node array limits
    if isempty(G.Nodes)
        cw.cells_0_nodes = [];
    else
        NodeTable = G.Nodes;
        num_nodes = height(NodeTable);
        nodes_array = cell(1, num_nodes);
        for i = 1:num_nodes
            t_val = NodeTable.type{i}; 
            if iscell(t_val), t_val = t_val{1}; end
            
            nodes_array{i} = struct('node_id', NodeTable.node_id(i), ...
                'type', t_val, ...
                'coord', NodeTable.coord(i,:));
        end
        cw.cells_0_nodes = nodes_array;
    end
    
    % Serialize Edge structural paths
    if isempty(G.Edges)
        cw.cells_1_linestrings = [];
    else
        EdgeTable = G.Edges;
        num_edges = height(EdgeTable);
        edges_array = cell(1, num_edges);
        for i = 1:num_edges
            src = EdgeTable.EndNodes(i, 1);
            tgt = EdgeTable.EndNodes(i, 2);
            
            rel_connects = EdgeTable.forest_relation_connects{i};
            if ~iscell(rel_connects), rel_connects = {rel_connects}; end
            
            edges_array{i} = struct( ...
                'line_id', EdgeTable.line_id(i), ...
                'endpoints', struct('source_id', src, 'target_id', tgt), ...
                'geometry', EdgeTable.geometry{i}, ...
                'forest_relation', struct('connects', {rel_connects}) ...
            );
        end
        cw.cells_1_linestrings = edges_array;
    end
    
    % Write seamlessly back out
    try
        json_str = jsonencode(cw, 'PrettyPrint', true);
    catch
        json_str = jsonencode(cw);
    end
    
    fid = fopen(out_path, 'w');
    if fid > 0
        fwrite(fid, json_str, 'char');
        fclose(fid);
        fprintf('Saved edited nested network perfectly to: %s\n', out_path);
    else
        error('Could not save to file bounds');
    end
end
