"""
validate_neuron_swc.py (neurite_detection)

Author: Samik Banerjee
Last updated on: August 28, 2026
GitHub: https://github.com/samik1986/um1_3d_volume/Neuron_Pipeline_Release

Validates the syntax of an SWC file and calculates topological graph metrics 
to verify if it physically resembles a valid neuron tree structure.
"""
import argparse
import os
import networkx as nx
import math
import numpy as np

def validate_swc(filepath):
    print(f"\n========================================================")
    print(f"Validating SWC: {os.path.basename(filepath)}")
    print(f"========================================================")
    if not os.path.exists(filepath):
        print("[FAIL] Error: File not found.")
        return
    
    nodes = {}
    edges = []
    
    # 1. Syntax Validation
    line_num = 0
    syntax_errors = 0
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line_num += 1
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) != 7:
                print(f"Syntax Error (Line {line_num}): Expected 7 columns, found {len(parts)}.")
                syntax_errors += 1
                continue
            
            try:
                n_id = int(parts[0])
                n_type = int(parts[1])
                x = float(parts[2])
                y = float(parts[3])
                z = float(parts[4])
                radius = float(parts[5])
                p_id = int(parts[6])
                
                nodes[n_id] = (x, y, z)
                # In SWC, parent id -1 means root node
                if p_id != -1:
                    edges.append((n_id, p_id))
            except ValueError:
                print(f"Syntax Error (Line {line_num}): Non-numeric values found.")
                syntax_errors += 1
    
    if syntax_errors > 0:
        print(f"\n[FAIL] Syntax Validation Failed with {syntax_errors} errors.")
        return
    else:
        print("[PASS] Syntax Validation: PASSED.")
    
    # 2. Graph Topological Validation
    G = nx.Graph()
    G.add_nodes_from(nodes.keys())
    # Add edges only if the parent actually exists in the node list
    valid_edges = [(u, v) for u, v in edges if v in nodes]
    missing_parents = len(edges) - len(valid_edges)
    
    if missing_parents > 0:
        print(f"[WARN] Graph Warning: {missing_parents} edges reference non-existent parent IDs.")
        
    G.add_edges_from(valid_edges)
    
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    
    if num_nodes == 0:
        print("[FAIL] Graph Validation: FAILED (Empty Graph).")
        return
        
    components = list(nx.connected_components(G))
    num_components = len(components)
    
    # Find cycles (meshes)
    try:
        cycles = nx.cycle_basis(G)
        num_cycles = len(cycles)
    except Exception as e:
        num_cycles = -1
        
    # Degrees
    degrees = dict(G.degree())
    endpoints = sum(1 for n, d in degrees.items() if d == 1)
    branchpoints = sum(1 for n, d in degrees.items() if d > 2)
    isolated = sum(1 for n, d in degrees.items() if d == 0)
    
    # Segment Lengths
    total_length = 0.0
    component_lengths = []
    
    for comp in components:
        comp_len = 0.0
        subgraph = G.subgraph(comp)
        for u, v in subgraph.edges():
            p1 = nodes[u]
            p2 = nodes[v]
            dist = math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 + (p1[2]-p2[2])**2)
            comp_len += dist
            total_length += dist
        component_lengths.append(comp_len)
        
    max_comp_length = max(component_lengths) if component_lengths else 0.0
    avg_comp_length = np.mean(component_lengths) if component_lengths else 0.0
    
    print("\n--- Graph Topological Metrics ---")
    print(f"Total Nodes       : {num_nodes}")
    print(f"Total Edges       : {num_edges}")
    print(f"Total Cable Length: {total_length:.2f} units")
    print(f"Max Component Len : {max_comp_length:.2f} units")
    print(f"Avg Component Len : {avg_comp_length:.2f} units")
    print(f"Isolated Nodes    : {isolated}")
    print(f"Fragments         : {num_components} (Ideal neurons have 1 main tree)")
    print(f"Cycles / Loops    : {num_cycles} (Ideal neurons have 0)")
    print(f"Endpoints (Leaves): {endpoints}")
    print(f"Branch Points     : {branchpoints}")
    
    # 3. Neuron Heuristic Check
    print("\n--- Biological Neuron Assessment ---")
    is_neuron = True
    
    # Cycle check
    if num_cycles > 0:
        print("[FAIL] Found cycles (meshes/spiderwebs). Real dendritic trees do not have loops.")
        is_neuron = False
    else:
        print("[PASS] No cycles detected. Topology is a valid tree/forest.")
        
    # Branching check
    if branchpoints == 0 and num_nodes > 10:
        print("[WARN] No branch points found. Looks like a single unbranched fiber.")
    elif branchpoints > 0:
        print("[PASS] Branching structure detected.")
        
    # Fragmentation check
    if num_components > max(20, num_nodes * 0.05):
        print(f"[FAIL] Too many disconnected fragments ({num_components}). Likely severe noise or bad thresholding.")
        is_neuron = False
    elif num_components > 1:
        print(f"[WARN] Tree is broken into {num_components} disconnected components.")
    else:
        print("[PASS] Single continuous connected component.")
        
    # Length check
    if max_comp_length < 100:
        print(f"[FAIL] Maximum continuous segment length is very small ({max_comp_length:.2f}). This indicates background noise speckles, not a long dendritic structure.")
        is_neuron = False
    else:
        print(f"[PASS] Primary structure has significant biological length ({max_comp_length:.2f} units).")
        
    if is_neuron:
        print("\n=> CONCLUSION: The SWC geometry mathematically resembles a valid neuron tree structure! [SUCCESS]")
    else:
        print("\n=> CONCLUSION: The SWC geometry has artifacts and DOES NOT resemble a clean neuron tree. [WARNING]")
    print("========================================================\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Validate SWC syntax and neuron topology.")
    parser.add_argument("swc_file", help="Path to the .swc file")
    args = parser.parse_args()
    validate_swc(args.swc_file)
