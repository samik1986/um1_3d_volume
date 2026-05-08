import React, { useState, useEffect, useMemo } from 'react';
import DeckGL from '@deck.gl/react';
import { OrbitView, OrthographicView } from '@deck.gl/core';
import { VolumeLayer, MultiscaleImageLayer, loadOmeZarr, ZarrPixelSource, RENDERING_MODES, getChannelStats } from '@hms-dbmi/viv';
import { PointCloudLayer } from '@deck.gl/layers';
import { openGroup } from 'zarr';

const INITIAL_VIEW_STATE_3D = {
  target: [0, 0, 0], // Center the camera at the origin (Viv VolumeLayer renders around origin)
  zoom: -3,
  rotationX: 0,
  rotationOrbit: 0,
};

const INITIAL_VIEW_STATE_2D = {
  target: [1360 * 0.1102, 1360 * 0.1102, 0],
  zoom: -2,
};

export default function App() {
  const [loader, setLoader] = useState<any>(null);
  const [centroids, setCentroids] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [show3D, setShow3D] = useState(true);
  const [show2D, setShow2D] = useState(true);
  
  // Intensity Windowing
  const [contrastMin, setContrastMin] = useState(0);
  const [contrastMax, setContrastMax] = useState(128); // Mid-range for uint8
  const [renderingMode, setRenderingMode] = useState(RENDERING_MODES.MAX_INTENSITY_PROJECTION);
  
  const [zSlice, setZSlice] = useState(135);

  useEffect(() => {
    async function init() {
      try {
        const zarrUrl = 'http://localhost:8001/volume.zarr';
        const centroidsUrl = 'http://localhost:8001/centroids.json';

        console.log("Starting load from", zarrUrl);

        let data;
        try {
            const res = await loadOmeZarr(zarrUrl, { type: 'multiscales' });
            data = res.data;
            console.log("Successfully loaded via loadOmeZarr", res);
        } catch (e) {
            console.warn("loadOmeZarr failed, trying manual multiscale parse...", e);
            const grp = await openGroup(zarrUrl);
            const scales = ['s0', 's1', 's2', 's3', 's4'];
            const loaders = await Promise.all(scales.map(async (s) => {
                const item = await grp.getItem(s);
                const viv = await import('@hms-dbmi/viv');
                return new (viv as any).ZarrPixelSource(item);
            }));
            data = loaders;
        }

        setLoader(data);

        // Auto-calculate Intensity Range
        try {
          const stats = await getChannelStats({ loader: data[0], selections: [{ t: 0, c: 0, z: 135 }] });
          if (stats && stats[0]) {
            const { mean, stdDev } = stats[0];
            setContrastMax(Math.min(255, Math.round(mean + stdDev * 2)));
            setContrastMin(Math.max(0, Math.round(mean - stdDev)));
          }
        } catch (e) {
          console.warn("Auto-stats calculation failed", e);
        }

        // Load Centroids
        const cRes = await fetch(centroidsUrl);
        if (cRes.ok) {
          const cData = await cRes.json();
          setCentroids(cData);
        }
      } catch (err: any) {
        console.error("Critical initialization error:", err);
        setError(err.message);
      }
    }
    init();
  }, []);

  const layers = useMemo(() => {
    if (!loader || loader.length < 4) return [];

    const volLayer = new VolumeLayer({
      id: 'volume-layer-3d',
      loader: [loader[3]], 
      resolution: 0,  
      colormap: 'gray',
      opacity: 1.0,
      colors: [[255, 255, 255]],
      domain: [[0, 255]],
      contrastLimits: [[contrastMin, contrastMax]],
      channelsVisible: [true],
      selections: [{ t: 0, c: 0 }],
      renderingMode: renderingMode,
      visible: show3D
    });

    const sliceLayer = new MultiscaleImageLayer({
      id: 'volume-layer-2d',
      loader: loader, 
      colormap: 'gray',
      colors: [[255, 255, 255]],
      domain: [[0, 255]],
      contrastLimits: [[contrastMin, contrastMax]],
      channelsVisible: [true],
      selections: [{ t: 0, c: 0, z: zSlice }],
      modelMatrix: new Float32Array([
        0.1102, 0, 0, 0,
        0, 0.1102, 0, 0,
        0, 0, 1, 0,
        0, 0, 0, 1
      ]),
      visible: show2D
    });

    const centroidLayer = new PointCloudLayer({
      id: 'centroid-layer',
      data: centroids,
      getPosition: (d: any) => [d.x * 0.1102, d.y * 0.1102, d.z * 0.5],
      getFillColor: [255, 0, 0],
      getRadius: 2,
      visible: show3D
    });

    return [volLayer, sliceLayer, centroidLayer];
  }, [loader, centroids, show3D, show2D, contrastMin, contrastMax, zSlice, renderingMode]);

  if (error) return <div style={{ color: 'red', padding: '20px' }}>Error: {error}</div>;
  if (!loader) return <div style={{ color: 'white', padding: '20px' }}>Loading Dataset... (Check Console for progress)</div>;

  return (
    <div style={{ width: '100vw', height: '100vh', display: 'flex', backgroundColor: '#000', overflow: 'hidden', fontFamily: 'sans-serif' }}>
      {/* Sidebar */}
      <div style={{ width: '300px', padding: '25px', backgroundColor: '#111', borderRight: '1px solid #333', color: 'white', zIndex: 10, display: 'flex', flexDirection: 'column' }}>
        <h2 style={{ margin: '0 0 10px 0', color: '#3b82f6' }}>Zarr Viewer</h2>
        <p style={{ fontSize: '0.8em', color: '#666', margin: '0 0 20px 0' }}>OME-Zarr Native Engine</p>
        <hr style={{ border: 'none', borderTop: '1px solid #333', marginBottom: '20px' }} />
        
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '10px', fontSize: '0.9em' }}>Min Intensity: {contrastMin}</label>
          <input 
            type="range" min="0" max="255" value={contrastMin} 
            onChange={(e) => setContrastMin(parseInt(e.target.value))}
            style={{ width: '100%', cursor: 'pointer' }}
          />
        </div>

        <div style={{ marginBottom: '25px' }}>
          <label style={{ display: 'block', marginBottom: '10px', fontSize: '0.9em' }}>Max Intensity: {contrastMax}</label>
          <input 
            type="range" min="0" max="255" value={contrastMax} 
            onChange={(e) => setContrastMax(parseInt(e.target.value))}
            style={{ width: '100%', cursor: 'pointer' }}
          />
        </div>

        <div style={{ marginBottom: '25px' }}>
          <label style={{ display: 'block', marginBottom: '10px', fontSize: '0.9em' }}>Rendering Mode</label>
          <select 
            value={renderingMode} 
            onChange={(e) => setRenderingMode(e.target.value)}
            style={{ width: '100%', padding: '8px', backgroundColor: '#222', color: 'white', border: '1px solid #444' }}
          >
            <option value={RENDERING_MODES.MAX_INTENSITY_PROJECTION}>MIP (Standard)</option>
            <option value={RENDERING_MODES.ADDITIVE}>Additive (Brightest)</option>
          </select>
        </div>

        <div style={{ marginBottom: '25px' }}>
          <label style={{ display: 'block', marginBottom: '10px', fontSize: '0.9em' }}>Z-Slice: {zSlice}</label>
          <input 
            type="range" min="0" max="270" value={zSlice} 
            onChange={(e) => setZSlice(parseInt(e.target.value))}
            style={{ width: '100%', cursor: 'pointer' }}
          />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.9em', cursor: 'pointer' }}>
            <input type="checkbox" checked={show3D} onChange={() => setShow3D(!show3D)} /> Show 3D Volume
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.9em', cursor: 'pointer' }}>
            <input type="checkbox" checked={show2D} onChange={() => setShow2D(!show2D)} /> Show 2D Slice
          </label>
        </div>
      </div>

      <div style={{ flex: 1, display: 'flex', position: 'relative' }}>
        <div style={{ flex: 1, position: 'relative', borderRight: '1px solid #222' }}>
          <DeckGL
            id="view3d"
            views={new OrbitView({ id: '3d', controller: true })}
            initialViewState={INITIAL_VIEW_STATE_3D}
            layers={layers.filter(l => l.id !== 'volume-layer-2d')}
          />
        </div>
        <div style={{ flex: 1, position: 'relative' }}>
          <DeckGL
            id="view2d"
            views={new OrthographicView({ id: '2d', controller: true })}
            initialViewState={INITIAL_VIEW_STATE_2D}
            layers={layers.filter(l => l.id === 'volume-layer-2d')}
          />
        </div>
      </div>
    </div>
  );
}
