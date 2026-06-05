# ☁️ How to Access the Cloud Proofreading Portal

Welcome to the Cloud Proofreading Interface! This document explains how you can log into the secure cloud server from any web browser in the world to perform structural proofreading on biological datasets.

## 1. Navigating to the Portal
Your lab administrator will provide you with a secure web link. This link will look something like:
`https://123.45.67.89.nip.io`

- Open this link in **Google Chrome**, **Firefox**, or **Microsoft Edge**.
- Because this is a heavy 3D rendering application, we do not recommend using mobile browsers.

## 2. Authentication
This portal is protected by **Google OAuth2** to ensure data security.
- When you visit the link, you will be redirected to a standard "Sign in with Google" page.
- Enter your approved Google email address and password.
- Once authenticated, you will be automatically securely tunneled to the cloud virtual machine.

## 3. The Virtual Interface (Napari)
Upon successful login, you will instantly see the **Napari 3D interface** streaming directly inside your browser window. 
- You do **not** need to install Python, CuPy, or any 3D rendering software on your personal computer.
- The cloud server's physical NVIDIA GPU handles all the rendering and mathematically intense operations for you.

## 4. Browser Navigation Controls
Because you are interacting with a streamed 3D desktop, use the following controls to navigate the 3D space:
- **Rotate 3D**: Click and drag the left mouse button anywhere in the black canvas.
- **Pan**: Hold `Shift` + click and drag.
- **Zoom**: Scroll your mouse wheel up and down.
- **Toggle Visibility**: Click the small "Eye" icon next to any layer in the bottom-left corner to hide or show it.

## 5. Next Steps
Once you are logged in, refer to the specific tool guide depending on your current task:
- See **`HOW_TO_PROOFREAD_NEURITES.md`** if you are editing the topological CW Complex network.
- See **`HOW_TO_PROOFREAD_CENTROIDS.md`** if you are performing cell-counting or editing `.swc` coordinates.
