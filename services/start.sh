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

start_service() {
  name="$1"

  if command -v systemctl >/dev/null 2>&1; then
    echo "[start.sh] Starting ${name}.service via systemctl"
    if command -v sudo >/dev/null 2>&1; then
      sudo systemctl daemon-reload >/dev/null 2>&1 || true
      sudo systemctl start "${name}.service"
    else
      systemctl daemon-reload >/dev/null 2>&1 || true
      systemctl start "${name}.service"
    fi
    systemctl --no-pager status "${name}.service" --lines=5 || true
    return 0
  fi

  case "$name" in
    ollama)
      echo "[start.sh] Starting Ollama API without preloading any model"
      exec "$PROJECT_ROOT/src/lib/ollama/dist/bin/ollama" serve
      ;;
    web)
      echo "[start.sh] Starting web server"
      exec sh "$PROJECT_ROOT/services/web.server.sh" "${PORT:-8000}"
      ;;
  esac
}

start_service ollama
start_service web
