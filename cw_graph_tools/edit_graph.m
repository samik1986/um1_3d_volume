function G = edit_graph(G, op, varargin)
    % EDIT_GRAPH Main evaluation wrapper dynamically natively routing graph manipulation operations.
    % Supported ops: 'add_node', 'delete_node', 'add_edge', 'delete_edge'
    
    switch lower(op)
        case 'add_node'
            % expected args: node_id, type ('boundary' or 'junction'), coord [Y, X]
            if nargin < 5, error('add_node requires node_id, type, coord'); end
            n_id = varargin{1};
            t_typ = varargin{2};
            coord = varargin{3};
            
            % Generate Table row natively mapped strictly
            NodeProps = table(n_id, {t_typ}, coord, 'VariableNames', {'node_id', 'type', 'coord'});
            G = addnode(G, NodeProps);
            
        case 'delete_node'
            % expected args: node_id
            n_idx = find(G.Nodes.node_id == varargin{1}, 1);
            if ~isempty(n_idx)
                G = rmnode(G, n_idx);
            end
            
        case 'add_edge'
            % expected: source_node_id, target_node_id, geometry, line_id
            src_id = varargin{1};
            tgt_id = varargin{2};
            geom = varargin{3};
            l_id = varargin{4};
            
            s_idx = find(G.Nodes.node_id == src_id, 1);
            t_idx = find(G.Nodes.node_id == tgt_id, 1);
            if isempty(s_idx) || isempty(t_idx)
                error('Source or Target missing natively map limits');
            end
            
            s_typ = G.Nodes.type{s_idx}; if iscell(s_typ), s_typ = s_typ{1}; end
            t_typ = G.Nodes.type{t_idx}; if iscell(t_typ), t_typ = t_typ{1}; end
            
            rel_conn = {s_typ, t_typ};
            
            EdgeProps = table([s_idx, t_idx], l_id, {geom}, {rel_conn}, ...
                'VariableNames', {'EndNodes', 'line_id', 'geometry', 'forest_relation_connects'});
            G = addedge(G, EdgeProps);
            
        case 'delete_edge'
            % expected logical bounds: line_id
            l_id = varargin{1};
            e_idx = find(G.Edges.line_id == l_id, 1);
            if ~isempty(e_idx)
                G = rmedge(G, e_idx);
            end
            
        otherwise
            error('Unrecognised graphing manipulation sequence evaluated');
    end
end
