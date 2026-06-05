# ☁️ Cloud Proofreading Deployment

This directory contains everything needed to deploy the Napari Proofreading Viewer as a **Secure Cloud Web Service** with hardware GPU acceleration and Google Authentication.

## 🚀 One-Click Deployment

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

## 🖥️ Bare-Metal Server Setup

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

## ⚙️ Configuration Requirements

Before your first deployment, you must configure the environment variables so that the Secure HTTPS Gateway (Caddy) and Google Login function correctly. 

1. Copy `.env.example` to a new file named `.env`.
2. Set the `SERVER_IP` to your machine's public IP address. (Caddy uses this to magically generate a free, valid Let's Encrypt SSL certificate via `nip.io`).
3. Generate an OAuth 2.0 Web Application credential in the **Google Cloud Console**.
4. Set the `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in the `.env` file. (Make sure your Authorized Redirect URI in Google matches the `SERVER_IP.nip.io` domain).
5. Set `TOOL_MODE` to `neurite` (for the topological CW Complex editor) or `centroids` (for the Cell Centroid proofreader).
6. Set the `DATA_DIR` in the `.env` file to point to the local folder on your VM where the TIFFs and JSONs are stored.

Once the `.env` is configured, running the 1-click deployment script will bring the secure website online!

---

## 🔄 Version Control (CI/CD)

Whenever you push code to the `main` branch of this repository on GitHub, a GitHub Action automatically triggers. It will build a fresh Docker image of the Napari streaming container and push it to Docker Hub. 

Because of this, you only ever need to run `./deploy_cloud.sh` on your VM to instantly pull down the latest features and restart the server!
