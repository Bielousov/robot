#!/bin/sh
set -eu

SCRIPT_PATH="${0}"
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$SCRIPT_PATH")" && pwd)"
PROJECT_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"
OLLAMA_HOST="${OLLAMA_HOST:-127.0.0.1:11434}"
OLLAMA_URL="http://${OLLAMA_HOST}"
WEB_PORT="${PORT:-8000}"
OLLAMA_LOG="/tmp/robot-ollama.log"
WEB_LOG="/tmp/robot-web.log"

assert_running() {
  name="$1"
  pattern="$2"
  log_file="$3"
  startup_delay="${4:-3}"

  sleep "$startup_delay"

  if pgrep -af "$pattern" >/dev/null 2>&1; then
    echo "[start.sh] $name started and is still running."
    return 0
  fi

  echo "[start.sh] ERROR: $name did not stay alive after launch."
  echo "[start.sh] Expected pattern: $pattern"
  echo "[start.sh] Log file: $log_file"

  if [ -f "$log_file" ]; then
    echo "[start.sh] --- $name log tail ---"
    tail -n 50 "$log_file"
    echo "[start.sh] --- end $name log ---"
  else
    echo "[start.sh] No log file was written at $log_file"
  fi

  echo "[start.sh] Diagnostic hints:"
  echo "[start.sh]  - confirm the binary exists and is executable"
  echo "[start.sh]  - check the .env and env values used by the process"
  echo "[start.sh]  - check filesystem permissions and port availability"
  echo "[start.sh]  - verify the launcher script can run under the target user"
  exit 1
}

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
  nohup env "OLLAMA_HOST=${OLLAMA_HOST}" "OLLAMA_MODELS=${PROJECT_ROOT}/src/lib/ollama/models" "$OLLAMA_BIN" serve >"$OLLAMA_LOG" 2>&1 &
  assert_running "Ollama" "ollama serve|/src/lib/ollama/dist/bin/ollama" "$OLLAMA_LOG" 3
else
  echo "[start.sh] Ollama is already running."
fi

echo "[start.sh] Starting web server"
nohup sh "$WEB_SERVER" "$WEB_PORT" >"$WEB_LOG" 2>&1 &
assert_running "Web" "web/server.sh|python3.*http.server|python3.*PORT.*OLLAMA_URL" "$WEB_LOG" 3

echo "[start.sh] Ollama and web services startup commands were issued."
exit 0
