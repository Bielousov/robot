#!/usr/bin/env python3

import http.server
import json
import os
import socketserver
import sys
import urllib.error
import urllib.request
from pathlib import Path


# ---------------------------------------------------------------------------
# Paths / configuration
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
WEB_DIR = SCRIPT_DIR

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8001

HAILO_HOST = os.environ.get("HAILO_HOST", "127.0.0.1:8000")
HAILO_URL = f"http://{HAILO_HOST}"

HAILO_MODEL = os.environ.get(
    "HAILO_MODEL",
    "qwen2.5:1.5B",
)


# ---------------------------------------------------------------------------
# Hailo-Ollama helpers
# ---------------------------------------------------------------------------

def hailo_request(path, method="GET", body=None, timeout=300):
    data = None

    headers = {
        "Content-Type": "application/json",
    }

    if body is not None:
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(
        f"{HAILO_URL}{path}",
        data=data,
        headers=headers,
        method=method,
    )

    return urllib.request.urlopen(request, timeout=timeout)


def ensure_model():
    """Ensure the configured Hailo model is available."""

    print(f"[Web] Hailo-Ollama: {HAILO_URL}")
    print(f"[Web] Hailo model:  {HAILO_MODEL}")

    try:
        with hailo_request("/api/tags", timeout=10) as response:
            data = json.loads(response.read())

        models = {
            model.get("name")
            for model in data.get("models", [])
        }

        if HAILO_MODEL in models:
            print(f"[Web] Hailo model already available: {HAILO_MODEL}")
            return

        print(f"[Web] Hailo model not found locally: {HAILO_MODEL}")
        print(f"[Web] Pulling model...")

        with hailo_request(
            "/api/pull",
            method="POST",
            body={
                "model": HAILO_MODEL,
                "stream": True,
            },
            timeout=600,
        ) as response:

            while True:
                line = response.readline()

                if not line:
                    break

                line = line.decode("utf-8", errors="replace").strip()

                if not line:
                    continue

                try:
                    message = json.loads(line)

                    if "error" in message:
                        raise RuntimeError(message["error"])

                    status = message.get("status")

                    if status:
                        print(f"[Web] Hailo pull: {status}")

                except json.JSONDecodeError:
                    print(f"[Web] Hailo pull: {line}")

        print(f"[Web] Hailo model ready: {HAILO_MODEL}")

    except Exception as error:
        print(
            f"[Web] ERROR: Could not initialize Hailo model: {error}",
            file=sys.stderr,
        )
        raise


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------

class RobotWebHandler(http.server.SimpleHTTPRequestHandler):

    def _proxy_api_request(self):
        content_length = int(
            self.headers.get("Content-Length", "0")
        )

        body = (
            self.rfile.read(content_length)
            if content_length
            else None
        )

        request = urllib.request.Request(
            f"{HAILO_URL}{self.path}",
            data=body,
            headers={
                "Content-Type": self.headers.get(
                    "Content-Type",
                    "application/json",
                ),
            },
            method=self.command,
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=300,
            ) as response:

                self.send_response(response.status)

                content_type = response.headers.get(
                    "Content-Type",
                    "application/json",
                )

                self.send_header(
                    "Content-Type",
                    content_type,
                )

                # Do not send Content-Length for streaming responses.
                if "text" not in content_type.lower() and \
                "ndjson" not in content_type.lower():
                    response_body = response.read()

                    self.send_header(
                        "Content-Length",
                        str(len(response_body)),
                    )

                    self.end_headers()
                    self.wfile.write(response_body)
                    self.wfile.flush()
                    return

                self.send_header(
                    "Cache-Control",
                    "no-cache",
                )
                self.send_header(
                    "Connection",
                    "keep-alive",
                )
                self.end_headers()

                while True:
                    chunk = response.read(8192)

                    if not chunk:
                        break

                    self.wfile.write(chunk)
                    self.wfile.flush()

        except urllib.error.HTTPError as error:
            response_body = error.read()

            self.send_response(error.code)
            self.send_header(
                "Content-Type",
                error.headers.get(
                    "Content-Type",
                    "application/json",
                ),
            )
            self.send_header(
                "Content-Length",
                str(len(response_body)),
            )
            self.end_headers()

            self.wfile.write(response_body)

        except urllib.error.URLError as error:
            response_body = json.dumps({
                "error": f"Hailo-Ollama unavailable: {error.reason}"
            }).encode("utf-8")

            self.send_response(502)
            self.send_header(
                "Content-Type",
                "application/json",
            )
            self.send_header(
                "Content-Length",
                str(len(response_body)),
            )
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


class ReuseAddrTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


# SimpleHTTPRequestHandler serves relative to the process cwd,
# so explicitly switch to web/.
os.chdir(WEB_DIR)


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"[Web] Project root: {PROJECT_ROOT}")
    print(f"[Web] Web directory: {WEB_DIR}")

    ensure_model()

    with ReuseAddrTCPServer(
        ("0.0.0.0", PORT),
        RobotWebHandler,
    ) as httpd:

        print(
            f"[Web] Server ready at "
            f"http://0.0.0.0:{PORT}"
        )

        httpd.serve_forever()