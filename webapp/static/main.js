document.addEventListener('DOMContentLoaded', () => {
    const localTiffInput = document.getElementById('localTiff');
    const localSwcInput = document.getElementById('localSwc');
    const loadLocalBtn = document.getElementById('loadLocalBtn');
    
    const uploadTiff = document.getElementById('uploadTiff');
    const uploadSwc = document.getElementById('uploadSwc');
    const uploadBtn = document.getElementById('uploadBtn');
    
    const statusPanel = document.getElementById('statusPanel');
    const layerControls = document.getElementById('layerControls');
    const zSlider = document.getElementById('zSlider');
    const zValue = document.getElementById('zValue');
    const togglePointsBtn = document.getElementById('togglePointsBtn');
    const toggleViewBtn = document.getElementById('toggleViewBtn');
    
    const sliceImage = document.getElementById('sliceImage');
    const pointsCanvas = document.getElementById('pointsCanvas');
    const viewer3d = document.getElementById('viewer3d');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const loadingText = document.getElementById('loadingText');
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    const ctx = pointsCanvas.getContext('2d');

    let metadata = null;
    let currentZ = 0;
    let currentPoints = [];
    let showPoints = true;

    // --- Loading Data ---
    loadLocalBtn.addEventListener('click', async () => {
        const payload = {
            tiff_path: localTiffInput.value.trim(),
            swc_path: localSwcInput.value.trim()
        };
        if (!payload.tiff_path) {
            alert("Please provide a TIFF path.");
            return;
        }
        await loadVolumeData('/api/load_local', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
    });

    uploadBtn.addEventListener('click', async () => {
        if (!uploadTiff.files.length) {
            alert("Please select a TIFF file.");
            return;
        }
        const formData = new FormData();
        formData.append('tiff_file', uploadTiff.files[0]);
        if (uploadSwc.files.length) {
            formData.append('swc_file', uploadSwc.files[0]);
        }
        await loadVolumeData('/api/upload', {
            method: 'POST',
            body: formData
        });
    });

    async function loadVolumeData(endpoint, options) {
        showLoading(true);
        try {
            const response = await fetch(endpoint, options);
            const data = await response.json();
            
            if (!response.ok || data.error) {
                throw new Error(data.error || "Failed to load data.");
            }

            metadata = data;
            statusPanel.innerHTML = `Loaded: ${metadata.width}x${metadata.height}x${metadata.num_slices}<br>Points: ${metadata.num_centroids}`;
            
            // Setup controls
            zSlider.max = metadata.num_slices - 1;
            zSlider.value = Math.floor(metadata.num_slices / 2);
            layerControls.style.display = 'block';
            sliceImage.style.display = 'block';
            
            await updateSlice(zSlider.value);

        } catch (err) {
            statusPanel.innerHTML = `<span style="color:var(--accent-red)">Error: ${err.message}</span>`;
        } finally {
            showLoading(false);
        }
    }

    // --- Interaction ---
    zSlider.addEventListener('input', (e) => {
        const z = e.target.value;
        zValue.innerText = `Z: ${z}`;
    });

    zSlider.addEventListener('change', async (e) => {
        await updateSlice(e.target.value);
    });

    let is3DMode = false;
    let threeInitialized = false;

    togglePointsBtn.addEventListener('click', () => {
        showPoints = !showPoints;
        if (showPoints) {
            togglePointsBtn.classList.add('active');
            togglePointsBtn.innerText = 'Hide Points';
        } else {
            togglePointsBtn.classList.remove('active');
            togglePointsBtn.innerText = 'Show Points';
        }
        drawPoints();
    });

    toggleViewBtn.addEventListener('click', async () => {
        is3DMode = !is3DMode;
        if (is3DMode) {
            toggleViewBtn.innerText = 'Switch to 2D Slice';
            sliceImage.style.display = 'none';
            pointsCanvas.style.display = 'none';
            viewer3d.style.display = 'block';
            
            if (!threeInitialized) {
                await initThreeJS();
            }
        } else {
            toggleViewBtn.innerText = 'Switch to 3D View';
            viewer3d.style.display = 'none';
            sliceImage.style.display = 'block';
            pointsCanvas.style.display = 'block';
        }
    });

    // --- Visualization ---
    async function updateSlice(z) {
        currentZ = z;
        showLoading(true);
        
        try {
            // Fetch points for this slice in parallel with image request
            const pointsReq = fetch(`/api/points/${z}`).then(r => r.json());
            
            // For image, we set the src. To know when it loads, we wait for onload
            const imageLoadPromise = new Promise((resolve, reject) => {
                sliceImage.onload = resolve;
                sliceImage.onerror = reject;
                // Add timestamp to prevent aggressive browser caching across different data sets
                sliceImage.src = `/api/slice/${z}?t=${new Date().getTime()}`;
            });

            const [points] = await Promise.all([pointsReq, imageLoadPromise]);
            currentPoints = points;
            
            // Sync canvas size to image natural size
            pointsCanvas.width = sliceImage.naturalWidth;
            pointsCanvas.height = sliceImage.naturalHeight;
            
            drawPoints();
        } catch (err) {
            console.error("Error updating slice:", err);
        } finally {
            showLoading(false);
        }
    }

    function drawPoints() {
        ctx.clearRect(0, 0, pointsCanvas.width, pointsCanvas.height);
        
        if (!showPoints || !currentPoints.length) return;

        // Draw points
        ctx.fillStyle = 'rgba(239, 68, 68, 0.8)'; // accent-red
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1;

        currentPoints.forEach(p => {
            ctx.beginPath();
            // p.r might be 1.0 default, make it a bit larger for visibility if needed
            const radius = Math.max(p.r, 3);
            ctx.arc(p.x, p.y, radius, 0, 2 * Math.PI);
            ctx.fill();
            ctx.stroke();
        });
    }

    function showLoading(show, text="Loading...", showProgress=false) {
        loadingOverlay.style.display = show ? 'flex' : 'none';
        loadingText.innerText = text;
        progressContainer.style.display = showProgress ? 'block' : 'none';
        if (showProgress) progressBar.style.width = '0%';
    }

    // --- Three.js 3D Viewer Logic ---
    async function initThreeJS() {
        showLoading(true, "Downsampling 3D Volume... (This may take a few seconds)", true);
        threeInitialized = true;
        
        // Setup polling for progress
        const progressInterval = setInterval(async () => {
            try {
                const res = await fetch('/api/volume3d_progress');
                if (res.ok) {
                    const data = await res.json();
                    if (data.progress >= 0) {
                        progressBar.style.width = data.progress + '%';
                        loadingText.innerText = `Processing 3D Volume... ${data.progress}%`;
                    }
                }
            } catch (e) {}
        }, 500);

        try {
            // Setup Three.js scene
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(45, viewer3d.clientWidth / viewer3d.clientHeight, 0.1, 1000);
            camera.position.set(0, 0, 2);
            
            const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
            renderer.setSize(viewer3d.clientWidth, viewer3d.clientHeight);
            viewer3d.appendChild(renderer.domElement);
            
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;

            // Fetch volume and points
            const [volRes, ptsRes] = await Promise.all([
                fetch('/api/volume3d'),
                fetch('/api/points_all')
            ]);
            
            clearInterval(progressInterval);
            progressBar.style.width = '100%';
            loadingText.innerText = "Rendering...";
            
            if (!volRes.ok) throw new Error("Failed to load 3D volume: " + await volRes.text());
            
            const dims = volRes.headers.get('X-Vol-Dim').split(',').map(Number);
            const w = dims[0], h = dims[1], d = dims[2];
            const buffer = await volRes.arrayBuffer();
            
            // 3D Texture
            const texture = new THREE.DataTexture3D(new Uint8Array(buffer), w, h, d);
            texture.format = THREE.RedFormat;
            texture.type = THREE.UnsignedByteType;
            texture.minFilter = THREE.LinearFilter;
            texture.magFilter = THREE.LinearFilter;
            texture.unpackAlignment = 1;
            texture.needsUpdate = true;
            
            const vertexShader = `
                out vec3 vOrigin;
                out vec3 vDirection;
                void main() {
                    vOrigin = vec3(inverse(modelMatrix) * vec4(cameraPosition, 1.0)).xyz;
                    vDirection = position - vOrigin;
                    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
                }
            `;
            
            const fragmentShader = `
                precision highp float;
                precision highp sampler3D;
                in vec3 vOrigin;
                in vec3 vDirection;
                out vec4 fragColor;
                uniform sampler3D u_data;
                
                vec2 hitBox(vec3 orig, vec3 dir) {
                    vec3 box_min = vec3(-0.5);
                    vec3 box_max = vec3(0.5);
                    vec3 inv_dir = 1.0 / dir;
                    vec3 tmin_tmp = (box_min - orig) * inv_dir;
                    vec3 tmax_tmp = (box_max - orig) * inv_dir;
                    vec3 tmin = min(tmin_tmp, tmax_tmp);
                    vec3 tmax = max(tmin_tmp, tmax_tmp);
                    float t0 = max(tmin.x, max(tmin.y, tmin.z));
                    float t1 = min(tmax.x, min(tmax.y, tmax.z));
                    return vec2(t0, t1);
                }
                
                void main() {
                    vec3 rayDir = normalize(vDirection);
                    vec2 bounds = hitBox(vOrigin, rayDir);
                    if (bounds.x > bounds.y) discard;
                    
                    bounds.x = max(bounds.x, 0.0);
                    vec3 p = vOrigin + bounds.x * rayDir;
                    vec3 inc = 1.0 / abs(rayDir);
                    float delta = min(inc.x, min(inc.y, inc.z)) / 200.0;
                    
                    float maxVal = 0.0;
                    for (float t = bounds.x; t < bounds.y; t += delta) {
                        float val = texture(u_data, p + 0.5).r;
                        maxVal = max(maxVal, val);
                        p += rayDir * delta;
                    }
                    if (maxVal < 0.05) discard;
                    fragColor = vec4(maxVal * 0.5, maxVal * 0.8, maxVal, maxVal * 0.6);
                }
            `;
            
            const material = new THREE.ShaderMaterial({
                uniforms: { u_data: { value: texture } },
                vertexShader: vertexShader,
                fragmentShader: fragmentShader,
                transparent: true,
                side: THREE.BackSide,
                glslVersion: THREE.GLSL3
            });
            
            // The aspect ratio of the volume bounds
            const maxDim = Math.max(w, h, d);
            const geometry = new THREE.BoxGeometry(w/maxDim, h/maxDim, d/maxDim);
            const mesh = new THREE.Mesh(geometry, material);
            scene.add(mesh);
            
            // Add points
            const pointsData = await ptsRes.json();
            if (pointsData.length > 0) {
                const ptsGeo = new THREE.BufferGeometry();
                const posArray = new Float32Array(pointsData.length * 3);
                pointsData.forEach((pt, i) => {
                    // Center and scale to match the BoxGeometry
                    posArray[i*3] = (pt.x / w - 0.5) * (w/maxDim);
                    // Three.js Y is up, but image Y is down, so we flip it
                    posArray[i*3+1] = -(pt.y / h - 0.5) * (h/maxDim);
                    posArray[i*3+2] = (pt.z / d - 0.5) * (d/maxDim);
                });
                ptsGeo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
                const ptsMat = new THREE.PointsMaterial({ color: 0xef4444, size: 0.015 });
                const pointsMesh = new THREE.Points(ptsGeo, ptsMat);
                scene.add(pointsMesh);
            }
            
            // Animation loop
            function animate() {
                requestAnimationFrame(animate);
                controls.update();
                renderer.render(scene, camera);
            }
            animate();
            
            window.addEventListener('resize', () => {
                if (!is3DMode) return;
                camera.aspect = viewer3d.clientWidth / viewer3d.clientHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(viewer3d.clientWidth, viewer3d.clientHeight);
            });
            
        } catch (err) {
            console.error(err);
            clearInterval(progressInterval);
            alert("Error loading 3D view: " + err.message);
        } finally {
            showLoading(false);
        }
    }
});
