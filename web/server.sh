#!/bin/sh

# Simple web server for robot web interface
# Serves web/index.html on http://localhost:8001

WEB_PORT="${1:-8001}"

SCRIPT_PATH="$0"
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$SCRIPT_PATH")" && pwd)"
PROJECT_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"

PYTHON_BIN="${PYTHON_BIN:-python3}"
SERVER_PY="$SCRIPT_DIR/server.py"

echo "Starting web server on http://0.0.0.0:$WEB_PORT"
echo "Serving files from: $SCRIPT_DIR"
echo "Using Python server: $SERVER_PY"
echo "Press Ctrl+C to stop"

if [ ! -f "$SERVER_PY" ]; then
    echo "ERROR: server.py not found: $SERVER_PY"
    exit 1
fi

exec "$PYTHON_BIN" "$SERVER_PY" "$WEB_PORT"