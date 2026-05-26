"""
launcher.py

A self-installing launcher for the Napari Centroid Proofreader.
Created by: Samik Banerjee @ Mitralab @ CSHL
It dynamically verifies, installs all required python dependencies, and runs the application.
"""

import sys
import subprocess
import importlib.util

REQUIRED_PACKAGES = {
    "numpy": "numpy",
    "pandas": "pandas",
    "tifffile": "tifffile",
    "qtpy": "qtpy",
    "magicgui": "magicgui",
    "napari": "napari[all]"  # Installs napari plus default Qt backend (PyQt5/PySide2)
}

def install_and_import(package_name, install_spec):
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        print(f"Missing dependency: '{install_spec}'. Installing now...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", install_spec])
            print(f"Successfully installed '{install_spec}'.")
        except subprocess.CalledProcessError as e:
            print(f"Error installing package '{install_spec}': {e}")
            sys.exit(1)
    else:
        print(f"Dependency '{package_name}' is already installed.")

def main():
    print("===================================================")
    # Print program signature on launch
    print("  3D Centroid Proofreader Launcher                ")
    print("  Created by: Samik Banerjee @ Mitralab @ CSHL    ")
    print("===================================================")
    print("Checking dependencies for 3D Centroid Proofreader...")
    
    # Check and install pip if missing
    try:
        import pip
    except ImportError:
        print("pip is missing! Attempting to bootstrap pip...")
        try:
            subprocess.check_call([sys.executable, "-m", "ensurepip", "--default-pip"])
        except Exception as e:
            print(f"Failed to bootstrap pip: {e}. Please ensure pip is installed.")
            sys.exit(1)

    # Install each required package
    for pkg_name, install_spec in REQUIRED_PACKAGES.items():
        install_and_import(pkg_name, install_spec)
        
    print("All dependencies checked and satisfied! Launching Napari Proofreader...")
    
    # Import and run proofreader main
    try:
        from napari_proofreader import main as launch_app
        launch_app()
    except Exception as e:
        print(f"Error running application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
