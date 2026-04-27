function [G, raw_json] = create_forest_from_json(json_path)
    % Reads a 1D CW Complex JSON and converts it natively to a MATLAB undirected graph
    % Preserves all geometric traces and topological properties dynamically.
    
    fid = fopen(json_path, 'r');
    if fid < 0
        error('Could not open file: %s', json_path);
    end
    raw_text = fscanf(fid, '%c');
    fclose(fid);
    
    raw_json = jsondecode(raw_text);
    
    nodes = raw_json.cells_0_nodes;
    edges = raw_json.cells_1_linestrings;
    
    if isempty(nodes)
        G = graph();
        return;
    end
    
    NodeTable = struct2table(nodes); 
    
    if isempty(edges)
        G = graph(NodeTable);
        return;
    end
    
    % Construct Edge properties mapping natively
    num_edges = length(edges);
    EndNodes = zeros(num_edges, 2);
    edge_geometries = cell(num_edges, 1);
    line_ids = zeros(num_edges, 1);
    connects_arr = cell(num_edges, 1);

    for i = 1:num_edges
        EndNodes(i, 1) = edges(i).endpoints.source_id;
        EndNodes(i, 2) = edges(i).endpoints.target_id;
        edge_geometries{i} = edges(i).geometry;
        line_ids(i) = edges(i).line_id;
        
        if isfield(edges(i), 'forest_relation') && isfield(edges(i).forest_relation, 'connects')
            connects_arr{i} = edges(i).forest_relation.connects;
        else
            connects_arr{i} = {};
        end
    end
    
    EdgeTable = table(EndNodes, line_ids, edge_geometries, connects_arr, ...
        'VariableNames', {'EndNodes', 'line_id', 'geometry', 'forest_relation_connects'});
        
    G = graph(EdgeTable, NodeTable);
end
