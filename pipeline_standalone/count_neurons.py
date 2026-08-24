import os

swc_path = r'c:\Users\banerjee\Desktop\um1_3d_volume\NEWFP_output\F0046_multichannel_cmle_ch03\skeletons_only.swc'

if not os.path.exists(swc_path):
    print("SWC file not found!")
else:
    count = 0
    total_nodes = 0
    with open(swc_path, 'r') as f:
        for line in f:
            if line.startswith('#'): continue
            parts = line.strip().split()
            if len(parts) >= 7:
                total_nodes += 1
                if parts[6] == '-1':
                    count += 1
                    
    print(f"Total SWC nodes: {total_nodes}")
    print(f"Number of independent neuron components (roots): {count}")
