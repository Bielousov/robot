#!/bin/bash

# Simple web server for robot web interface
# Serves web/index.html on http://localhost:8000

PORT=${1:-8000}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_DIR="$(dirname "$SCRIPT_DIR")/web"

echo "Starting web server on http://0.0.0.0:$PORT"
echo "Serving files from: $WEB_DIR"
echo "Press Ctrl+C to stop"

cd "$WEB_DIR" && python3 << 'PYTHON_EOF'
import http.server
import socketserver
import os

PORT = 8000
Handler = http.server.SimpleHTTPRequestHandler

class ReuseAddrTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

with ReuseAddrTCPServer(("0.0.0.0", PORT), Handler) as httpd:
    print(f"Server ready at http://0.0.0.0:{PORT}")
    httpd.serve_forever()
PYTHON_EOF
