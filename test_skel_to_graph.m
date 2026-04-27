clear; clc;
H = 100;
W = 100;
BW = false(H, W);

% Draw a 'Y' shape
% top left arm
for i=20:50
    BW(i, i) = true;
end
% top right arm
for i=20:50
    BW(i, 100-i) = true;
end
% vertical stem
for i=50:80
    BW(i, 50) = true;
end

% add a small spur to prune
for i=50:55
    BW(50, 50+i-50) = true;
end

skel_struct.H = H;
skel_struct.W = W;
[r, c] = find(BW);
skel_struct.coords = single([r, c]);

graph = skel_to_graph_2d(skel_struct, 10);

disp('Nodes:');
disp(graph.nodes);
disp('Node Types (1=End, 3=Junc):');
disp(graph.node_type);
disp('Edges:');
disp(graph.edges);
disp('Edge Paths length:');
for i=1:length(graph.edge_paths)
    fprintf(' Edge %d: %d pixels\n', i, size(graph.edge_paths{i}, 1));
end

fig = figure('Visible', 'off');
imshow(BW); hold on;
% plot edges
for i=1:length(graph.edge_paths)
    p = graph.edge_paths{i};
    plot(p(:,2), p(:,1), 'g-', 'LineWidth', 2);
end
% plot nodes
n = graph.nodes;
scatter(n(:,2), n(:,1), 50, graph.node_type, 'filled');
colormap(jet);
title('Graph topology');
saveas(fig, 'test_graph.png');
disp('Done');
