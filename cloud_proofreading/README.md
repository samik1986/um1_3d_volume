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

---

## ⚙️ Configuration Requirements

Before your first deployment, you must configure the Google Login authentication. 

1. Copy `.env.example` to a new file named `.env`.
2. Generate an OAuth 2.0 Web Application credential in the **Google Cloud Console**.
3. Set the `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in the `.env` file.
4. Set the `DATA_DIR` in the `.env` file to point to the local folder on your VM where the TIFFs and JSONs are stored.

Once the `.env` is configured, running the 1-click deployment script will bring the secure website online!

---

## 🔄 Version Control (CI/CD)

Whenever you push code to the `main` branch of this repository on GitHub, a GitHub Action automatically triggers. It will build a fresh Docker image of the Napari streaming container and push it to Docker Hub. 

Because of this, you only ever need to run `./deploy_cloud.sh` on your VM to instantly pull down the latest features and restart the server!
