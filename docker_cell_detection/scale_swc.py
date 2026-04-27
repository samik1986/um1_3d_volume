import pandas as pd
import os

def scale_swc(input_filename, output_filename, scale_x, scale_y, scale_z):
    if not os.path.exists(input_filename):
        print(f"Error: {input_filename} not found.")
        return

    print(f"Loading {input_filename}...")
    try:
        # SWC format: id type x y z radius parent
        # We need to preserve the header if possible, but standard SWC uses '#' for comments
        df = pd.read_csv(input_filename, sep=' ', comment='#', header=None, 
                         names=['id', 'type', 'x', 'y', 'z', 'r', 'p'])
        
        print(f"Scaling coordinates by ({scale_x}, {scale_y}, {scale_z})...")
        df['x'] = df['x'] * scale_x
        df['y'] = df['y'] * scale_y
        df['z'] = df['z'] * scale_z
        
        # Save to new file
        print(f"Saving to {output_filename}...")
        with open(output_filename, 'w') as f:
            f.write(f"# SWC file scaled from {input_filename}\n")
            f.write(f"# Scale factors: X={scale_x}, Y={scale_y}, Z={scale_z}\n")
            f.write("# id type x y z radius parent\n")
            # Write data rows
            # We use float format to preserve precision
            for index, row in df.iterrows():
                f.write(f"{int(row['id'])} {int(row['type'])} {row['x']:.6f} {row['y']:.6f} {row['z']:.6f} {row['r']:.6f} {int(row['p'])}\n")
        
        print("Done.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    scale_swc('centroids_FP.swc', 'centroids_FP_scaled.swc', 0.1102, 0.1102, 0.5)
