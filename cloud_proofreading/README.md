# Cloud Proofreading Deployment

This directory contains everything needed to deploy the Napari Proofreading Viewer as a Secure Cloud Web Service with hardware GPU acceleration and Google Authentication.

## One-Click Deployment

If you are running this on a cloud VM (like AWS EC2 or GCP), simply run one of the following execution scripts:

**For Linux/Ubuntu VMs:**
```bash
cd cloud_proofreading
./deploy_cloud.sh
```

**For Windows VMs:**
Double-click `deploy_cloud.bat`

### What the script does:
1. Validates that your `.env` configuration file exists.
2. Automatically pulls the latest `napari-cloud` Docker image from your Docker Hub registry.
3. Bootstraps the `docker-compose.yml` stack, turning on the Google OAuth gateway and the VNC server.

## Bare-Metal Server Setup

If you are starting from a completely fresh, empty Ubuntu Server (or physical machine) with an NVIDIA GPU, you do not need to manually install Docker or the GPU drivers.

Simply run the automated bootstrap script:
```bash
sudo ./bare_metal_setup/bootstrap_ubuntu_gpu.sh
```
This script will automatically:
1. Install Docker and Docker Compose.
2. Install the proprietary NVIDIA Drivers.
3. Install the NVIDIA Container Toolkit so Docker can access the GPU.
*Note: You must reboot the machine after running this script.*

---

## Configuration Requirements

Before your first deployment, you must configure the environment variables so that the Secure HTTPS Gateway (Caddy) and Google Login function correctly. 

1. Copy `.env.example` to a new file named `.env`.
2. Set the `SERVER_IP` to your machine's public IP address. (Caddy uses this to magically generate a free, valid Let's Encrypt SSL certificate via `nip.io`).
3. Generate an OAuth 2.0 Web Application credential in the Google Cloud Console.
4. Set the `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in the `.env` file. (Make sure your Authorized Redirect URI in Google matches the `SERVER_IP.nip.io` domain).
5. Set `TOOL_MODE` to `neurite` (for the topological CW Complex editor) or `centroids` (for the Cell Centroid proofreader).
6. Set the `DATA_DIR` in the `.env` file to point to the local folder on your VM where the TIFFs and JSONs are stored.

Once the `.env` is configured, running the 1-click deployment script will bring the secure website online!

---

## Version Control (CI/CD)

Whenever you push code to the `main` branch of this repository on GitHub, a GitHub Action automatically triggers. It will build a fresh Docker image of the Napari streaming container and push it to Docker Hub. 

Because of this, you only ever need to run `./deploy_cloud.sh` on your VM to instantly pull down the latest features and restart the server!

---

# Unified Proofreading Ecosystem Walkthrough

Welcome to the new and improved Unified Proofreading Ecosystem! Over the course of this development session, we have built a robust, hardware-accelerated proofreading suite that can be deployed securely in the cloud or run seamlessly on a local bare-metal workstation.

Below is a complete walkthrough of the architecture, features, and instructions on how to run both setups.

---

## 1. Architecture & Features

We completely rebuilt the proofreading tool into a Unified Viewer. Instead of having separate editors for Cell Centroids and Neurite Networks, both can now be edited simultaneously in the same viewport!

### Key Features
- **Unified Interface:** Load raw 3D TIFF volumes alongside Skeletons and Centroids simultaneously.
- **Format Agnostic:** Natively supports both `.swc` (standard neuron morphology format) and `.json` (topological CW-Complex graph) files for reading and saving.
- **Intensity-Based Medial Axis Snapping:** When you draw a new neurite connection and press `S` to save, the algorithm searches an 8x8x8 voxel neighborhood in the raw image volume. It finds the absolute highest intensity fluorophore signal and precisely snaps your drawn coordinates to that local maximum. This guarantees your traced skeletons hug the exact medial axis of the physical neurite!
- **Dynamic Tree Coloring (Graph Component Identification):** Every time you load the viewer or execute a snap, the system mathematically calculates the connected components of the entire skeleton graph. It instantly assigns distinct, vibrant colors to each unique "tree", providing you with immediate visual confirmation of whether a newly drawn branch successfully merged into the main structure.

---

## 2. Cloud Deployment Setup

The cloud setup utilizes a containerized stack to stream the hardware-accelerated Napari GUI directly into any web browser.

### Cloud Architecture
1. **napari_stream**: A custom Docker container that runs VirtualGL (`vglrun`) against your physical NVIDIA GPU, streaming the GUI over `x11vnc` to `noVNC` on port 8080.
2. **oauth2_proxy**: A secure authentication gateway that intercepts all traffic and forces users to log in with an approved Google Account.
3. **caddy**: A modern reverse proxy that automatically provisions and renews SSL/HTTPS certificates using `nip.io` DNS routing.

### How to Run the Cloud Setup

1. **Configure Environment:**
   Navigate to the `cloud_proofreading` folder and copy the template:
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file to include your Google OAuth credentials, your server's IP address, and configure the optional `INPUT_RAW`, `INPUT_SKELETONS`, and `INPUT_CENTROIDS` file paths.

2. **Launch the Stack:**
   ```bash
   docker-compose up -d --build
   ```

3. **Access the Tool:**
   Open a web browser and go to `https://<YOUR-SERVER-IP>.nip.io`. After authenticating with Google, the Unified Viewer will appear directly in your browser. If you did not specify default files in the `.env` file, the viewer will open blank and you can simply drag-and-drop files directly into the browser window!

---

## 3. Standalone Bare-Metal Setup

The exact same `unified_viewer.py` script that powers the cloud can be run natively on a local workstation. We built a highly user-friendly fallback mode specifically for this scenario.

### How to Run the Standalone Setup

If you are running this natively on a machine with Python and Napari installed, you do not need to use the command line to specify your files!

1. **Install Requirements:**
   If you have not already, install the necessary Python packages for the standalone viewer:
   ```bash
   pip install -r cloud_proofreading/requirements.txt
   ```

2. **Launch the Script:**
   Simply execute the script via terminal or your IDE:
   ```bash
   python cloud_proofreading/napari_stream/unified_viewer.py
   ```

3. **GUI Fallback Navigation:**
   Because you did not pass command line arguments (like `--raw`), the script intelligently detects it is running in standalone mode. It will automatically pop up native OS File Dialog Windows!
   - You will first be prompted to select your Raw Volume `.tif` file.
   - Next, it will prompt you for an optional Skeletons file (`.swc` or `.json`). You can hit Cancel to skip.
   - Finally, it will prompt you for an optional Centroids file (`.swc` or `.json`).

Once you finish the dialogs, Napari will launch natively on your desktop, utilizing your local GPU and all of the intensity-snapping and dynamic coloring logic!

---

## 4. On-Premise (Institutional / Intranet) Server Setup

If you want to host the streaming UI on an internal server (e.g., an institutional cluster) and access it via a web browser without public internet exposure or OAuth authentication, we provide a streamlined on-premise configuration.

### How to Run the On-Premise Setup

1. **Launch the Intranet Stack:**
   Navigate to the `cloud_proofreading` folder and run the deployment script:
   - On Linux/Mac:
     ```bash
     bash deploy_on_premise.sh
     ```
   - On Windows:
     ```cmd
     deploy_on_premise.bat
     ```

2. **Access the Tool Locally:**
   Open a web browser on any computer connected to your local network (LAN) or VPN and navigate to:
   ```
   http://<YOUR_LOCAL_SERVER_IP>:8080
   ```
   
This bypasses the Caddy HTTPS and Google OAuth proxies, exposing the Napari canvas directly to your internal network.
