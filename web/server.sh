#!/bin/sh

# Simple web server for robot web interface
# Serves web/index.html on http://localhost:8001

PORT="${1:-8001}"
SCRIPT_PATH="${0}"
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$SCRIPT_PATH")" && pwd)"
PROJECT_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
WEB_DIR="$PROJECT_ROOT/web"

echo "Starting web server on http://0.0.0.0:$PORT"
echo "Serving files from: $WEB_DIR"
echo "Press Ctrl+C to stop"

cd "$WEB_DIR" || exit 1
PORT="$PORT" exec python3 << 'PYTHON_EOF'
import http.server
import socketserver
import os
import json
import urllib.error
import urllib.request

PORT = int(os.environ.get("PORT", "8001"))
OLLAMA_URL = "http://127.0.0.1:11434"

class RobotWebHandler(http.server.SimpleHTTPRequestHandler):
    def _proxy_api_request(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length) if content_length else None
        request = urllib.request.Request(
            f"{OLLAMA_URL}{self.path}",
            data=body,
            headers={"Content-Type": self.headers.get("Content-Type", "application/json")},
            method=self.command,
        )

        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                response_body = response.read()
                self.send_response(response.status)
                self.send_header("Content-Type", response.headers.get("Content-Type", "application/json"))
                self.send_header("Content-Length", str(len(response_body)))
                self.end_headers()
                self.wfile.write(response_body)
        except urllib.error.HTTPError as error:
            response_body = error.read()
            self.send_response(error.code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)
        except urllib.error.URLError as error:
            response_body = json.dumps(
                {"error": f"Ollama unavailable: {error.reason}"}
            ).encode()
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)

    def do_POST(self):
        if self.path.startswith("/api/"):
            self._proxy_api_request()
        else:
            self.send_error(404)

    def do_GET(self):
        if self.path.startswith("/api/"):
            self._proxy_api_request()
        else:
            super().do_GET()

Handler = RobotWebHandler

class ReuseAddrTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

with ReuseAddrTCPServer(("0.0.0.0", PORT), Handler) as httpd:
    print(f"Server ready at http://0.0.0.0:{PORT}")
    httpd.serve_forever()
PYTHON_EOF
