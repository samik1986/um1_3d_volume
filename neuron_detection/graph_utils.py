"""
graph_utils.py (neuron_detection)

Author: Samik Banerjee
Date: May 8, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

Utilities for graph stitching, topological analysis, and serialization to CW-Complex and SWC formats.
"""

import networkx as nx
import numpy as np
import json
from scipy.spatial import cKDTree

def stitch_graphs(graph_list, merge_dist=2.0):
    """
    Merges multiple subvolume graphs into a single graph.
    Welds boundary nodes that are within `merge_dist`.
    """
    if not graph_list:
        return nx.MultiGraph()
        
    print(f"Stitching {len(graph_list)} graphs...")
    combined_graph = nx.MultiGraph()
    
    node_offset = 0
    for g in graph_list:
        mapping = {n: n + node_offset for n in g.nodes()}
        g_renamed = nx.relabel_nodes(g, mapping, copy=True)
        combined_graph.add_nodes_from(g_renamed.nodes(data=True))
        combined_graph.add_edges_from(g_renamed.edges(data=True))
        node_offset += len(g.nodes())
        
    print(f"  Total nodes before welding: {combined_graph.number_of_nodes()}")
    
    nodes = list(combined_graph.nodes())
    if not nodes:
        return combined_graph
        
    coords = np.array([combined_graph.nodes[n]['o'] for n in nodes])
    
    tree = cKDTree(coords)
    pairs = tree.query_pairs(r=merge_dist)
    
    merge_graph = nx.Graph()
    merge_graph.add_nodes_from(nodes)
    merge_graph.add_edges_from(pairs)
    
    components = list(nx.connected_components(merge_graph))
    node_mapping = {}
    
    for comp in components:
        comp_list = list(comp)
        keep_node = comp_list[0] 
        for n in comp_list:
            node_mapping[n] = keep_node
            
    final_graph = nx.relabel_nodes(combined_graph, node_mapping, copy=False)
    
    self_loops = list(nx.selfloop_edges(final_graph, keys=True))
    final_graph.remove_edges_from(self_loops)
    
    print(f"  Total nodes after welding: {final_graph.number_of_nodes()}")
    return final_graph

def graph_to_cw_complex(graph, out_file):
    """Saves the graph into the CW-Complex JSON format."""
    print(f"Saving CW-Complex to {out_file}...")
    nodes_list = []
    lines_list = []
    
    for node_id, data in graph.nodes(data=True):
        z, y, x = data['o']
        node_type = "boundary" if graph.degree(node_id) == 1 else "junction"
        nodes_list.append({
            "node_id": int(node_id),
            "type": node_type,
            "coord": [int(z), int(y), int(x)]
        })
        
    line_id = 1
    for u, v, key, data in graph.edges(keys=True, data=True):
        coords = data.get('pts', [])
        if len(coords) == 0:
            coords = [graph.nodes[u]['o'], graph.nodes[v]['o']]
            
        geom = [[int(pt[0]), int(pt[1]), int(pt[2])] for pt in coords]
        
        u_type = "boundary" if graph.degree(u) == 1 else "junction"
        v_type = "boundary" if graph.degree(v) == 1 else "junction"
        
        lines_list.append({
            "line_id": line_id,
            "endpoints": {"source_id": int(u), "target_id": int(v)},
            "geometry": geom,
            "forest_relation": {"connects": [u_type, v_type]}
        })
        line_id += 1
        
    cw_complex = {
        "network_type": "1D CW Complex Forest",
        "cells_0_nodes": nodes_list,
        "cells_1_linestrings": lines_list
    }
    
    with open(out_file, 'w') as f:
        json.dump(cw_complex, f, indent=2)

def graph_to_swc(graph, out_file):
    """Saves the graph to SWC format."""
    print(f"Saving SWC to {out_file}...")
    with open(out_file, 'w') as f:
        f.write("# id type x y z r pid\n")
        
        node_mapping = {}
        current_id = 1
        
        for n, data in graph.nodes(data=True):
            z, y, x = data['o']
            f.write(f"{current_id} 2 {x} {y} {z} 1.0 -1\n")
            node_mapping[n] = current_id
            current_id += 1
            
        for u, v, key, data in graph.edges(keys=True, data=True):
            pts = data.get('pts', [])
            if len(pts) <= 2:
                f.write(f"{current_id} 2 {graph.nodes[v]['o'][2]} {graph.nodes[v]['o'][1]} {graph.nodes[v]['o'][0]} 1.0 {node_mapping[u]}\n")
                current_id += 1
                continue
                
            prev_id = node_mapping[u]
            for pt in pts:
                z, y, x = pt
                f.write(f"{current_id} 2 {x} {y} {z} 1.0 {prev_id}\n")
                prev_id = current_id
                current_id += 1
                
            f.write(f"{current_id} 2 {graph.nodes[v]['o'][2]} {graph.nodes[v]['o'][1]} {graph.nodes[v]['o'][0]} 1.0 {prev_id}\n")
            current_id += 1
