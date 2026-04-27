# CW Graph Tools
*A standalone native JSON spatial evaluation and topological manipulation toolkit.*

This package interacts directly with `1D CW Complex` JSON files representing pure continuous graphical subsets inherently ignoring built-in MATLAB graphing limitations.

## Core Operations

To load and interact securely:
```matlab
addpath('cw_graph_tools');
cw_json = load_cw_json('fp_pipeline_output/SubVol1_Angle000_cw_complex.json');

% Evaluates plotting mathematically overlaying boundaries physically using pchip splines!
plot_cw_complex(cw_json);
```

## Analytical Structural Extraction 
We provide mathematically explicit evaluations executing pure DFS and Kruskal's constraints bounding natively over raw struct properties directly.
```matlab
% Synthesizes structural rings detecting cyclic paths directly.
loops_json = find_loops(cw_json);

% Distils subsets inherently matching physical mathematical geometric minimal Euclidean trees.
mst_json = find_mst(cw_json);
```

## Array Matrix Manipulators
Dynamically structure properties mutating pure isolated graph components explicitly.
```matlab
% Eliminates all matrix lines tracing physically back to node limit 108 natively.
edited_json = delete_tree(cw_json, 108);

% Union isolated structures completely abstracting target array identifiers to prevent bounding overlap safely.
merged_json = add_tree(cw_json_base, cw_json_added);

% Save limits perfectly back to Euclidean geometry serialization logic.
save_cw_json(merged_json, 'fp_pipeline_output/SubVol1_Edited_Complex.json');
```

## Internal 1D CW-Complex JSON Spec

This format inherently stores pure components physically mapping exact boundary intersection limits securely over continuous lines preventing internal string overlaps mathematically natively exactly explicitly mapping limits!

- `network_type`: Usually "1D CW Complex Forest"
- `cells_0_nodes`: Array containing structures physically holding `node_id`, `type`, and `coord[y, x]`. Type is restricted mathematically bounded strictly uniformly evaluating `"boundary"` natively tracking `"junction"`.
- `cells_1_linestrings`: Array encoding discrete physical path limits natively dynamically matching variables identifying structural strings uniquely linking coordinates. Contains explicit properties:
    - `"line_id"`
    - `"endpoints"` (`source_id`, `target_id`)
    - `"geometry"` (Array of array tuples evaluating spatial coordinates mapping physically natively matching path trajectories!)
    - `"forest_relation"` (Abstractly connecting bounds string logic natively dynamically)
