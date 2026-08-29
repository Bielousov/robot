#!/bin/sh
set -eu

SCRIPT_PATH="${0}"
PROJECT_ROOT="$(CDPATH= cd -- "$(dirname -- "$SCRIPT_PATH")" && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

if [ -f "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a
fi

OLLAMA_BIN="$PROJECT_ROOT/src/lib/ollama/dist/bin/ollama"
WEB_SERVER="$PROJECT_ROOT/services/web.server.sh"

if [ ! -x "$OLLAMA_BIN" ]; then
  echo "[start.sh] Ollama binary not found or not executable: $OLLAMA_BIN"
  exit 1
fi

if [ ! -f "$WEB_SERVER" ]; then
  echo "[start.sh] Web server script not found: $WEB_SERVER"
  exit 1
fi

echo "[start.sh] Starting Ollama API without preloading any model"
"$OLLAMA_BIN" serve &
OLLAMA_PID=$!

trap 'kill "$OLLAMA_PID" 2>/dev/null || true' EXIT INT TERM

echo "[start.sh] Starting web server"
exec sh "$WEB_SERVER" "${PORT:-8000}"
