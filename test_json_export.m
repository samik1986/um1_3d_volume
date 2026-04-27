addpath('fp_pipeline_modules');
graph_data.nodes = [10 10; 50 10; 10 50];
graph_data.node_type = [1; 3; 1];
graph_data.edges = [1 2; 3 2];
graph_data.edge_paths = { [10 10; 20 10; 30 10; 40 10; 50 10], [10 50; 10 40; 10 30; 10 20; 50 10] };
export_cw_complex_json(graph_data, 'test_output');
