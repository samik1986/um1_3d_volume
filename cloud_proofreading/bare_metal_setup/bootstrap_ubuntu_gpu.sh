#!/bin/bash
set -e

echo "================================================================"
echo "🚀 Bootstrapping Bare-Metal Ubuntu Server for Cloud Proofreading"
echo "================================================================"

# Ensure script is run as root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root (sudo ./bootstrap_ubuntu_gpu.sh)"
  exit 1
fi

echo "1. Updating system packages..."
apt-get update && apt-get upgrade -y

echo "2. Installing Docker & Docker Compose..."
# Install Docker
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-compose

echo "3. Installing NVIDIA Drivers..."
apt-get install -y ubuntu-drivers-common
ubuntu-drivers autoinstall

echo "4. Installing NVIDIA Container Toolkit..."
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
apt-get update
apt-get install -y nvidia-container-toolkit

echo "Configuring Docker to use NVIDIA runtime..."
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker

echo "================================================================"
echo "✅ Server Bootstrapping Complete!"
echo "Please REBOOT the server to load the new NVIDIA kernel modules."
echo "After reboot, navigate to the cloud_proofreading folder, configure your .env, and run ./deploy_cloud.sh"
echo "================================================================"
