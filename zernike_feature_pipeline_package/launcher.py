"""
launcher.py

Self-contained dependency bootstrap and launcher for the Zernike 3D Batch Feature Extraction Pipeline.
Created by: Samik Banerjee @ Mitralab @ CSHL
"""

import sys
import os
import subprocess
import importlib.util

# Packages required to run the Zernike extraction pipeline
REQUIRED_PACKAGES = {
    "numpy": "numpy",
    "pandas": "pandas",
    "tifffile": "tifffile",
    "scipy": "scipy",
    "cupy": "cupy" # Note: cupy installation dynamically requires CUDA compatibility
}

def install_package(install_spec):
    print(f"Missing dependency: '{install_spec}'. Bootstrapping installation...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", install_spec])
        print(f"Successfully installed '{install_spec}'.")
    except subprocess.CalledProcessError as e:
        # Fallback in case cupy standard installation fails due to missing direct CUDA-SDK
        if "cupy" in install_spec:
            print("Standard CuPy installation failed. Attempting cupy-cuda coordinate fallback (cupy-cuda12x)...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "cupy-cuda12x"])
                return
            except subprocess.CalledProcessError:
                pass
        print(f"Error: Failed to auto-install package '{install_spec}': {e}")
        sys.exit(1)

def main():
    print("=========================================================")
    print("  Zernike 3D Feature Extraction Pipeline Launcher        ")
    print("  Created by: Samik Banerjee @ Mitralab @ CSHL           ")
    print("=========================================================")
    print("Verifying pipeline Python dependencies...")

    # Ensure pip is initialized
    try:
        import pip
    except ImportError:
        print("pip is missing! Initializing pip bootstrap...")
        try:
            subprocess.check_call([sys.executable, "-m", "ensurepip", "--default-pip"])
        except Exception as e:
            print(f"Failed to bootstrap pip: {e}. Please ensure pip is installed.")
            sys.exit(1)

    # Scan and install packages
    for pkg_name, install_spec in REQUIRED_PACKAGES.items():
        spec = importlib.util.find_spec(pkg_name)
        if spec is None:
            install_package(install_spec)
        else:
            print(f"Dependency '{pkg_name}' is already installed.")

    print("\nAll dependencies checked and satisfied! Launching Zernike Pipeline...\n")
    
    # Run the modular extraction pipeline
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pipeline_script = os.path.join(script_dir, "batch_process_zernike.py")
    
    # Forward any arguments from launcher.py call directly to batch_process_zernike.py
    cmd = [sys.executable, pipeline_script] + sys.argv[1:]
    subprocess.run(cmd)

if __name__ == '__main__':
    main()
