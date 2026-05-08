"""
serve_zarr.py (zarr_viewer)

Author: Samik Banerjee
Date: May 8, 2026
GitHub: https://github.com/samik1986/um1_3d_volume

Minimal multi-threaded HTTP server with CORS enabled for serving 
Zarr datasets to web frontends.
"""

import http.server
import socketserver

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Range, Content-Type, Authorization, X-Requested-With')
        self.send_header('Access-Control-Expose-Headers', 'Content-Length, Content-Range')
        self.send_header('Access-Control-Allow-Private-Network', 'true')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

PORT = 8001
Handler = CORSRequestHandler

print(f"Serving Zarr on port {PORT} with CORS enabled (Multi-threaded)...")
with socketserver.ThreadingTCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
