#!/bin/sh
set -eu

WEB_PORT="${1:-8001}"

SCRIPT_PATH="$0"
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$SCRIPT_PATH")" && pwd)"
PROJECT_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"

ENV_FILE="$PROJECT_ROOT/.env"
SERVER_PY="$SCRIPT_DIR/server.py"

HAILO_HOST="${HAILO_HOST:-127.0.0.1:8000}"
HAILO_URL="http://${HAILO_HOST}"
HAILO_BIN="${HAILO_BIN:-$(command -v hailo-ollama || true)}"

HAILO_LOG="/tmp/robot-hailo-ollama.log"


if [ -f "$ENV_FILE" ]; then
    set -a
    . "$ENV_FILE"
    set +a
fi

HAILO_HOST="${HAILO_HOST:-127.0.0.1:8000}"
HAILO_URL="http://${HAILO_HOST}"


echo "Starting web server on http://0.0.0.0:$WEB_PORT"
echo "Serving files from: $SCRIPT_DIR"
echo "Hailo-Ollama: $HAILO_URL"
echo "Hailo model: ${HAILO_MODEL:-Qwen2.5-1.5B-Instruct}"
echo "Using Python server: $SERVER_PY"


if [ ! -f "$SERVER_PY" ]; then
    echo "[server.sh] ERROR: server.py not found: $SERVER_PY"
    exit 1
fi


if [ -z "$HAILO_BIN" ]; then
    echo "[server.sh] ERROR: hailo-ollama not found in PATH."
    exit 1
fi


if ! curl -fsS "$HAILO_URL/api/version" >/dev/null 2>&1; then
    echo "[server.sh] Starting Hailo-Ollama..."

    nohup env \
        "OLLAMA_HOST=$HAILO_HOST" \
        "$HAILO_BIN" \
        >"$HAILO_LOG" 2>&1 &

    HAILO_PID=$!

    echo "[server.sh] Hailo-Ollama PID: $HAILO_PID"

    started=0

    i=0
    while [ "$i" -lt 30 ]; do
        if curl -fsS "$HAILO_URL/api/version" >/dev/null 2>&1; then
            started=1
            break
        fi

        if ! kill -0 "$HAILO_PID" 2>/dev/null; then
            echo "[server.sh] ERROR: Hailo-Ollama exited during startup."
            echo "[server.sh] --- Hailo-Ollama log ---"
            tail -n 50 "$HAILO_LOG" 2>/dev/null || true
            echo "[server.sh] --- end log ---"
            exit 1
        fi

        sleep 1
        i=$((i + 1))
    done

    if [ "$started" -ne 1 ]; then
        echo "[server.sh] ERROR: Hailo-Ollama did not become ready."
        echo "[server.sh] --- Hailo-Ollama log ---"
        tail -n 50 "$HAILO_LOG" 2>/dev/null || true
        echo "[server.sh] --- end log ---"
        exit 1
    fi

    echo "[server.sh] Hailo-Ollama is ready."
else
    echo "[server.sh] Hailo-Ollama is already running."
fi


echo "[server.sh] Starting Python web server..."

exec python3 "$SERVER_PY" "$WEB_PORT"