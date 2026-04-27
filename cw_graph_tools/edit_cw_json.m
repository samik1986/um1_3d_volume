function new_json = edit_cw_json(cw_json, op, varargin)
    % EDIT_CW_JSON Direct logical struct array mapping limits uniquely overriding mathematical abstractions.
    % Supported ops: 'add_node', 'delete_node', 'add_edge', 'delete_edge'
    
    new_json = cw_json;
    switch lower(op)
        case 'add_node'
            % args: node_id, type ('boundary' or 'junction'), coord [Y, X]
            n_node = struct('node_id', varargin{1}, 'type', varargin{2}, 'coord', varargin{3});
            if isfield(new_json, 'cells_0_nodes') && ~isempty(new_json.cells_0_nodes)
                new_json.cells_0_nodes(end+1) = n_node;
            else
                new_json.cells_0_nodes = n_node;
            end
            
        case 'delete_node'
            n_idx = [];
            for i = 1:length(new_json.cells_0_nodes)
                if new_json.cells_0_nodes(i).node_id == varargin{1}
                    n_idx = i; break;
                end
            end
            if ~isempty(n_idx)
                new_json.cells_0_nodes(n_idx) = [];
            end
            
        case 'add_edge'
            % args: source_node_id, target_node_id, geometry, line_id
            s_id = varargin{1}; t_id = varargin{2};
            
            s_t = 'junction'; t_t = 'junction';
            for i = 1:length(new_json.cells_0_nodes)
                if new_json.cells_0_nodes(i).node_id == s_id
                    s_t = new_json.cells_0_nodes(i).type;
                end
                if new_json.cells_0_nodes(i).node_id == t_id
                    t_t = new_json.cells_0_nodes(i).type;
                end
            end
            
            n_edge = struct('line_id', varargin{4}, ...
                            'endpoints', struct('source_id', s_id, 'target_id', t_id), ...
                            'geometry', varargin{3}, ...
                            'forest_relation', struct('connects', {{s_t, t_t}}));
                            
            if isfield(new_json, 'cells_1_linestrings') && ~isempty(new_json.cells_1_linestrings)
                new_json.cells_1_linestrings(end+1) = n_edge;
            else
                new_json.cells_1_linestrings = n_edge;
            end
            
        case 'delete_edge'
            e_idx = [];
            for i = 1:length(new_json.cells_1_linestrings)
                if new_json.cells_1_linestrings(i).line_id == varargin{1}
                    e_idx = i; break;
                end
            end
            if ~isempty(e_idx)
                new_json.cells_1_linestrings(e_idx) = [];
            end
            
        otherwise
            error('Unrecognised structural sequence strictly limits json.');
    end
end
