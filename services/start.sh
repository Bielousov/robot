#!/bin/sh
set -eu

SCRIPT_PATH="${0}"
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$SCRIPT_PATH")" && pwd)"
PROJECT_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"
OLLAMA_HOST="${OLLAMA_HOST:-127.0.0.1:11434}"
OLLAMA_URL="http://${OLLAMA_HOST}"
WEB_PORT="${PORT:-8000}"

if [ -f "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a
fi

OLLAMA_BIN="$PROJECT_ROOT/src/lib/ollama/dist/bin/ollama"
WEB_SERVER="$PROJECT_ROOT/web/server.sh"

if [ ! -x "$OLLAMA_BIN" ]; then
  echo "[start.sh] Ollama binary not found or not executable: $OLLAMA_BIN"
  exit 1
fi

if [ ! -f "$WEB_SERVER" ]; then
  echo "[start.sh] Web server script not found: $WEB_SERVER"
  exit 1
fi

if ! curl -fsS "${OLLAMA_URL}/api/version" >/dev/null 2>&1; then
  echo "[start.sh] Starting Ollama API without preloading any model"
  nohup env "OLLAMA_HOST=${OLLAMA_HOST}" "OLLAMA_MODELS=${PROJECT_ROOT}/src/lib/ollama/models" "$OLLAMA_BIN" serve >/tmp/robot-ollama.log 2>&1 &
else
  echo "[start.sh] Ollama is already running."
fi

echo "[start.sh] Starting web server"
nohup sh "$WEB_SERVER" "$WEB_PORT" >/tmp/robot-web.log 2>&1 &

echo "[start.sh] Ollama and web services startup commands were issued."
exit 0
