"""
launch.py (zarr_viewer)

Author: Samik Banerjee
Date: May 8, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

Main launch script for the Zarr viewer. 
Starts both the backend data server and the Vite React frontend.
"""

import subprocess
import webbrowser
import time
import sys
import os

def main():
    print("========================================")
    print("    Starting 3D Biological Viewer...    ")
    print("========================================")

    # Start the Python Zarr Server
    print("-> Starting Python Zarr Data Server on port 8001...")
    python_proc = subprocess.Popen([sys.executable, "serve_zarr.py"])

    # Start the Vite React Frontend Server
    print("-> Starting Vite React Frontend Server on port 5173...")
    # Use shell=True on Windows so 'npm' resolves correctly from PATH
    vite_proc = subprocess.Popen(["npm", "run", "dev"], cwd="frontend", shell=True)

    # Wait a few seconds for the servers to spin up
    print("-> Waiting for servers to initialize...")
    time.sleep(4)

    # Open the default web browser
    print("-> Opening Web Browser to http://localhost:5173...")
    webbrowser.open("http://localhost:5173")

    print("\n========================================")
    print("Servers are running! Keep this window open.")
    print("Press Ctrl+C to shut down both servers.")
    print("==========================================\n")

    try:
        # Keep the script alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Shutting down servers...")
        python_proc.terminate()
        vite_proc.terminate()
        print("[!] Done.")

if __name__ == "__main__":
    main()
