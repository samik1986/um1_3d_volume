function new_json = delete_tree(cw_json, target_node_id)
    % DELETE_TREE Eradicates bounding limits identifying sub-structural physical boundaries intersecting queries avoiding object models completely natively.
    
    new_json = cw_json;
    if isempty(cw_json.cells_0_nodes) || isempty(cw_json.cells_1_linestrings)
        return;
    end
    
    nodes = cw_json.cells_0_nodes;
    edges = cw_json.cells_1_linestrings;
    num_nodes = length(nodes);
    num_edges = length(edges);
    
    % Node idx mapping
    id_to_idx = containers.Map('KeyType', 'double', 'ValueType', 'double');
    for i = 1:num_nodes
        id_to_idx(nodes(i).node_id) = i;
    end
    
    if ~id_to_idx.isKey(target_node_id)
        warning('Logical target node subset completely missing from mapped array structure.');
        return;
    end
    
    % Adjacency lists structuring arrays natively natively
    adj = cell(num_nodes, 1);
    for i = 1:num_edges
        src = edges(i).endpoints.source_id;
        tgt = edges(i).endpoints.target_id;
        u = id_to_idx(src);
        v = id_to_idx(tgt);
        
        if isempty(adj{u}), adj{u} = v; else, adj{u}(end+1) = v; end
        if isempty(adj{v}), adj{v} = u; else, adj{v}(end+1) = u; end
    end
    
    % BFS isolation targeting strictly local connected branches natively
    visited = false(num_nodes, 1);
    queue = id_to_idx(target_node_id);
    visited(queue) = true;
    
    while ~isempty(queue)
        curr = queue(1);
        queue(1) = [];
        
        neighbors = adj{curr};
        if ~isempty(neighbors)
            for n_idx = 1:numel(neighbors)
                nxt = neighbors(n_idx);
                if ~visited(nxt)
                    visited(nxt) = true;
                    queue(end+1) = nxt;
                end
            end
        end
    end
    
    % Mask generating logical structures to cull
    keep_nodes = ~visited;
    keep_edges = true(num_edges, 1);
    
    for i = 1:num_edges
        src = edges(i).endpoints.source_id;
        tgt = edges(i).endpoints.target_id;
        if visited(id_to_idx(src)) || visited(id_to_idx(tgt))
            keep_edges(i) = false;
        end
    end
    
    % Inject modifications natively rewriting matrices directly avoiding arrays dynamically
    new_json.cells_0_nodes = nodes(keep_nodes);
    new_json.cells_1_linestrings = edges(keep_edges);
    
    fprintf('Custom structural isolation completely extracted bounding disconnected matrices precisely logically bounding components natively.\n');
end
