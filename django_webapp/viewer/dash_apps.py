"""
dash_apps.py (django_webapp viewer)

Author: Samik Banerjee
Date: May 8, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

Dash-based 3D visualization components using Dash-VTK. 
Integrated into the Django application for high-performance 3D rendering.
"""

import dash_vtk
from dash import html, dcc, Input, Output, State, no_update
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import numpy as np
import tifffile
import pandas as pd
import math
import plotly.express as px

app = DjangoDash('CellViewer3D', external_stylesheets=[dbc.themes.BOOTSTRAP])

# Global state to hold volume and data
volume_data = {
    'tif': None,
    'pages': None,
    'shape': None,
    'num_slices': 0,
    'centroids': pd.DataFrame(columns=['id', 'type', 'x', 'y', 'z', 'r', 'p']),
    'downsampled': None
}

def parse_swc(filepath):
    try:
        df = pd.read_csv(filepath, sep=' ', comment='#', header=None, 
                         names=['id', 'type', 'x', 'y', 'z', 'r', 'p'], skipinitialspace=True)
        return df.dropna()
    except Exception as e:
        print(f"Error reading SWC: {e}")
        return pd.DataFrame(columns=['id', 'type', 'x', 'y', 'z', 'r', 'p'])

sidebar = html.Div(
    [
        html.H2("CellViewer 3D", className="text-primary"),
        html.P("Dash-VTK Native Engine", className="text-muted", style={"fontSize": "0.9em", "marginTop": "-10px"}),
        html.Hr(style={"borderColor": "#444"}),
        
        dbc.Label("TIFF Path"),
        dbc.Input(id="tiff-path", value="../docker_cell_detection/F0200_multichannel_cmle_ch04.tif", className="mb-3", style={"background": "#222", "color": "white", "border": "none"}),
        
        dbc.Label("SWC Path"),
        dbc.Input(id="swc-path", value="../docker_cell_detection/centroids_DAPI.swc", className="mb-3", style={"background": "#222", "color": "white", "border": "none"}),
        
        dbc.Row([
            dbc.Col([dbc.Label("X Res", style={"fontSize":"0.8em"}), dbc.Input(id="res-x", value=0.1102, type="number", step=0.0001, style={"background": "#222", "color": "white", "border": "none", "padding":"5px"})]),
            dbc.Col([dbc.Label("Y Res", style={"fontSize":"0.8em"}), dbc.Input(id="res-y", value=0.1102, type="number", step=0.0001, style={"background": "#222", "color": "white", "border": "none", "padding":"5px"})]),
            dbc.Col([dbc.Label("Z Res", style={"fontSize":"0.8em"}), dbc.Input(id="res-z", value=0.5, type="number", step=0.0001, style={"background": "#222", "color": "white", "border": "none", "padding":"5px"})])
        ], className="mb-3"),
        
        dbc.Button("Load Volume", id="load-btn", color="primary", className="w-100 mb-3"),
        html.Div(id="load-status", className="mb-4 text-warning", style={"fontSize": "0.9em"}),
        
        dbc.Label("Visibility", className="fw-bold mt-2"),
        dbc.Checklist(
            options=[
                {"label": "Show 3D Volume", "value": "vol"},
                {"label": "Show Detections", "value": "det"},
                {"label": "Show 2D Slice", "value": "slice"},
            ],
            value=["vol", "det"],
            id="visibility-toggle",
            switch=True,
            style={"color": "white"}
        ),
        
        html.Div(
            [
                dbc.Label("3D Opacity Adjust", className="mt-3 fw-bold text-success"),
                dcc.Slider(
                    id="opacity-slider",
                    min=100, max=8000, step=100, value=2500,
                    marks=None,
                    tooltip={"placement": "bottom", "always_visible": False}
                )
            ]
        ),
        
        html.Div(
            [
                dbc.Label("Z-Slice Index", className="mt-4 fw-bold text-info"),
                dcc.Slider(
                    id="z-slider",
                    min=0, max=100, step=1, value=50,
                    marks=None,
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ],
            id="slider-container",
            style={"display": "none"}
        )
    ],
    style={
        "width": "320px",
        "padding": "20px",
        "backgroundColor": "#1a1a1a",
        "borderRight": "1px solid #333",
        "height": "100vh",
        "overflowY": "auto",
        "boxSizing": "border-box"
    }
)

app.layout = html.Div([
    sidebar,
    html.Div([
        html.Div(
            dcc.Loading(
                type="circle",
                color="#3b82f6",
                children=[
                    dash_vtk.View(id='view-3d', background=[0, 0, 0], interactorSettings=[
                        {"button": 1, "action": "Rotate"},
                        {"button": 2, "action": "Pan"},
                        {"button": 3, "action": "Pan"},
                        {"button": 1, "action": "Zoom", "control": True},
                        {"button": 1, "action": "Pan", "shift": True},
                    ])
                ]
            ),
            id='vtk-container-3d', 
            style={'flex': 1, 'background': '#000', 'height': '100%', 'position': 'relative'}
        ),
        html.Div(
            dcc.Loading(
                type="circle",
                color="#3b82f6",
                children=[
                    dcc.Graph(id='graph-2d', responsive=True, style={'height': '100%', 'width': '100%'}, config={'scrollZoom': True, 'displayModeBar': False})
                ]
            ),
            id='vtk-container-2d', 
            style={'flex': 1, 'background': '#111', 'height': '100%', 'position': 'relative', 'borderLeft': '2px solid #333'}
        )
    ], id='dual-pane-container', style={'display': 'flex', 'flex': 1, 'height': '100vh', 'width': '100%', 'overflow': 'hidden'})
], style={'display': 'flex', 'height': '100vh', 'width': '100vw', 'overflow': 'hidden'})


@app.callback(
    [Output("load-status", "children"), Output("z-slider", "max"), Output("z-slider", "value")],
    [Input("load-btn", "n_clicks")],
    [State("tiff-path", "value"), State("swc-path", "value"),
     State("res-x", "value"), State("res-y", "value"), State("res-z", "value")]
)
def load_data(n_clicks, tiff_path, swc_path, res_x, res_y, res_z):
    if not n_clicks:
        if volume_data.get('num_slices') > 0:
            max_z = volume_data['num_slices'] - 1
            return "Loaded.", max_z, max_z//2
        return "Ready.", 100, 50
        
    try:
        if tiff_path:
            volume_data['tif'] = tifffile.TiffFile(tiff_path)
            volume_data['pages'] = volume_data['tif'].pages
            volume_data['num_slices'] = len(volume_data['pages'])
            h, w = volume_data['pages'][0].shape
            
            num_slices = volume_data['num_slices']
            z_step = max(1, num_slices // 150)
            xy_step = max(1, w // 300)
            
            slices = list(range(0, num_slices, z_step))
            z_dim = len(slices)
            out_h = int(math.ceil(h / xy_step))
            out_w = int(math.ceil(w / xy_step))
            
            downsampled = np.zeros((z_dim, out_h, out_w), dtype=np.float32)
            
            for i, z in enumerate(slices):
                img_arr = volume_data['pages'][z].asarray().astype(np.float32)
                sub_arr = img_arr[::xy_step, ::xy_step]
                sh, sw = sub_arr.shape
                downsampled[i, :sh, :sw] = sub_arr
                
            p2, p98 = np.percentile(downsampled, (2, 98))
            downsampled = np.clip((downsampled - p2) / (p98 - p2 + 1e-5), 0, 1)
            downsampled = (downsampled * 255).astype(np.uint8)
            
            volume_data['downsampled'] = downsampled
            volume_data['steps'] = (z_step, xy_step)
            
        if swc_path:
            volume_data['centroids'] = parse_swc(swc_path)
            
        volume_data['res'] = (float(res_x), float(res_y), float(res_z))
        max_z = volume_data['num_slices'] - 1
        return "Loaded successfully!", max_z, max_z // 2
    except Exception as e:
        return f"Error: {str(e)}", 100, 50


@app.callback(
    Output("slider-container", "style"),
    [Input("visibility-toggle", "value")]
)
def toggle_slider(visibility):
    if "slice" in visibility:
        return {"display": "block"}
    return {"display": "none"}


@app.callback(
    [Output('vtk-container-3d', 'style'), Output('vtk-container-2d', 'style')],
    [Input('visibility-toggle', 'value')]
)
def update_styles(visibility):
    show_3d = "vol" in visibility or "det" in visibility
    show_2d = "slice" in visibility
    
    style_3d = {
        'flex': 1 if show_3d else 0,
        'width': '100%' if show_3d else '0px',
        'visibility': 'visible' if show_3d else 'hidden',
        'background': '#000', 'height': '100%', 'position': 'relative',
        'overflow': 'hidden'
    }
    style_2d = {
        'flex': 1 if show_2d else 0,
        'width': '100%' if show_2d else '0px',
        'visibility': 'visible' if show_2d else 'hidden',
        'background': '#111', 'height': '100%', 'position': 'relative',
        'borderLeft': '2px solid #333' if (show_3d and show_2d) else 'none',
        'overflow': 'hidden'
    }
    return style_3d, style_2d


@app.callback(
    Output('view-3d', 'children'),
    [Input("load-status", "children"), Input('visibility-toggle', 'value'), Input('opacity-slider', 'value')]
)
def render_3d(status, visibility, opacity_range):
    if volume_data.get('downsampled') is None:
        return []
        
    downsampled = volume_data['downsampled']
    z_dim, h, w = downsampled.shape
    flat_array = downsampled.flatten(order='C')
    
    res_x, res_y, res_z = volume_data.get('res', (0.1102, 0.1102, 0.5))
    z_step, xy_step = volume_data['steps']
    physical_spacing = [res_x * xy_step, res_y * xy_step, res_z * z_step]
    
    children_3d = []
    
    image_data = dash_vtk.ImageData(
        dimensions=[w, h, z_dim],
        spacing=physical_spacing,
        origin=[0, 0, 0],
        children=[
            dash_vtk.PointData([
                dash_vtk.DataArray(
                    registration="setScalars",
                    values=flat_array
                )
            ])
        ]
    )
    
    if "vol" in visibility:
        children_3d.append(
            dash_vtk.VolumeRepresentation(
                mapper={"blendMode": 0},
                colorMapPreset="Grayscale",
                colorDataRange=[0, opacity_range],
                property={"shade": False},
                children=[
                    dash_vtk.VolumeController(),
                    image_data
                ]
            )
        )
        
    points = volume_data.get('centroids')
    if points is not None and not points.empty and "det" in visibility:
        res_x, res_y, res_z = volume_data.get('res', (0.1102, 0.1102, 0.5))
        coords = []
        verts = []
        for i, (_, row) in enumerate(points.iterrows()):
            coords.extend([row['x'] * res_x, row['y'] * res_y, row['z'] * res_z])
            verts.extend([1, i])
            
        geom = dash_vtk.GeometryRepresentation(
            property={"color": [1, 0, 0], "pointSize": 15},
            children=[
                dash_vtk.PolyData(
                    points=coords,
                    verts=verts
                )
            ]
        )
        children_3d.append(geom)
        
    return children_3d


@app.callback(
    Output('graph-2d', 'figure'),
    [Input("load-status", "children"), Input('visibility-toggle', 'value'), Input('z-slider', 'value')]
)
def render_2d(status, visibility, z_slice):
    if volume_data.get('tif') is None or "slice" not in visibility:
        return no_update
        
    pages = volume_data['pages']
    if z_slice < 0 or z_slice >= len(pages):
        return no_update
        
    # Extract exact full resolution slice dynamically
    img_arr = pages[z_slice].asarray().astype(np.float32)
    
    # Fast min-max percentile norm
    p2, p98 = np.percentile(img_arr, (2, 98))
    img_arr = np.clip((img_arr - p2) / (p98 - p2 + 1e-5), 0, 1)
    img_arr = (img_arr * 255).astype(np.uint8)
    
    fig = px.imshow(img_arr, color_continuous_scale='gray')
    fig.update_layout(
        autosize=True,
        margin=dict(l=0, r=0, b=0, t=0),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        coloraxis_showscale=False,
        plot_bgcolor='#111',
        paper_bgcolor='#111'
    )
    return fig
