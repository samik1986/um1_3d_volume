function graph = skel_to_graph_2d(skeleton_struct, prune_length)
    % SKEL_TO_GRAPH_2D Converts a binary sparse skeleton to a topological graph.
    % graph nodes: endpoints (type 1) and branch/junction points (type 3)
    % graph edges: paths connecting nodes
    %
    % Inputs:
    %   skeleton_struct: struct with .coords (Nx2 single), .H, .W
    %   prune_length: min branch length for pruning (pixels)
    
    if nargin < 2
        prune_length = 0;
    end
    
    H = skeleton_struct.H;
    W = skeleton_struct.W;
    
    % Reconstruct dense logical
    BW = false(H, W);
    if isempty(skeleton_struct.coords)
        graph.nodes = [];
        graph.node_type = [];
        graph.edges = [];
        graph.edge_paths = {};
        return;
    end
    
    coords = double(skeleton_struct.coords);
    % Prevent out of bounds
    r = coords(:,1); c = coords(:,2);
    valid = r >= 1 & r <= H & c >= 1 & c <= W;
    r = r(valid); c = c(valid);
    
    lin_idx = sub2ind([H, W], r, c);
    BW(lin_idx) = true;
    
    % Pruning
    if prune_length > 0
        BW = bwskel(logical(BW), 'MinBranchLength', prune_length);
    else
        BW = bwskel(logical(BW)); % Ensure canonical 1-pixel thickness
    end
    
    if ~any(BW(:))
        graph.nodes = [];
        graph.node_type = [];
        graph.edges = [];
        graph.edge_paths = {};
        return;
    end
    
    % Find morphology
    EP = bwmorph(BW, 'endpoints');
    BP = bwmorph(BW, 'branchpoints');
    
    % Cluster branchpoints (bwmorph junction outputs can be thick)
    BP_cc = bwconncomp(BP, 8);
    num_junc = BP_cc.NumObjects;
    
    [ep_r, ep_c] = find(EP);
    num_ep = length(ep_r);
    
    % Allocate nodes
    nodes_r = zeros(num_junc + num_ep, 1);
    nodes_c = zeros(num_junc + num_ep, 1);
    node_type = zeros(num_junc + num_ep, 1); % 1=endpoint, 3=junction
    
    for i = 1:num_junc
        [jr, jc] = ind2sub([H, W], BP_cc.PixelIdxList{i});
        nodes_r(i) = mean(jr);
        nodes_c(i) = mean(jc);
        node_type(i) = 3;
    end
    
    for i = 1:num_ep
        idx = num_junc + i;
        nodes_r(idx) = ep_r(i);
        nodes_c(idx) = ep_c(i);
        node_type(idx) = 1;
    end
    
    % Extract edges by removing branch points
    paths_bw = BW;
    paths_bw(BP) = false; 
    paths_cc = bwconncomp(paths_bw, 8);
    
    edges = zeros(0, 2);
    edge_paths = {};
    edge_idx = 1;
    
    % Node map to easily lookup node idx by pixel
    node_map = zeros(H, W);
    for i = 1:num_junc
        node_map(BP_cc.PixelIdxList{i}) = i;
    end
    for i = 1:num_ep
        node_map(ep_r(i), ep_c(i)) = num_junc + i;
    end
    
    for i = 1:paths_cc.NumObjects
        path_pixels = paths_cc.PixelIdxList{i};
        [pr, pc] = ind2sub([H, W], path_pixels);
        
        dr = [-1; -1; -1; 0; 0; 1; 1; 1];
        dc = [-1; 0; 1; -1; 1; -1; 0; 1];
        R = pr' + dr;
        C = pc' + dc;
        valid = R >= 1 & R <= H & C >= 1 & C <= W;
        R = R(valid);
        C = C(valid);
        neighbor_idx = sub2ind([H, W], R, C);
        
        connected_nodes = unique(node_map(neighbor_idx));
        connected_nodes(connected_nodes == 0) = [];
        
        if length(connected_nodes) == 2
            edges(edge_idx, :) = [connected_nodes(1), connected_nodes(2)];
            edge_paths{edge_idx} = single([pr, pc]);
            edge_idx = edge_idx + 1;
        elseif length(connected_nodes) == 1
            % Self-loop or a branch connected to only one node (e.g. artifact)
            edges(edge_idx, :) = [connected_nodes(1), connected_nodes(1)];
            edge_paths{edge_idx} = single([pr, pc]);
            edge_idx = edge_idx + 1;
        elseif length(connected_nodes) > 2
            % Path touches more than 2 nodes. Pick the 2 closest ends.
            % But since it's an 8-connected single path, we just pick first 2.
            edges(edge_idx, :) = [connected_nodes(1), connected_nodes(2)];
            edge_paths{edge_idx} = single([pr, pc]);
            edge_idx = edge_idx + 1;
        end
    end
    
    graph.nodes = single([nodes_r, nodes_c]);
    graph.node_type = node_type;
    graph.edges = edges;
    graph.edge_paths = edge_paths;
end
