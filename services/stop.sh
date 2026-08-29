#!/bin/sh
set -eu

stop_service() {
  name="$1"

  if command -v systemctl >/dev/null 2>&1; then
    echo "[stop.sh] Stopping ${name}.service via systemctl"
    if command -v sudo >/dev/null 2>&1; then
      sudo systemctl stop "${name}.service" || true
    else
      systemctl stop "${name}.service" || true
    fi
  fi

  case "$name" in
    ollama)
      echo "[stop.sh] Stopping Ollama API"
      pkill -f "ollama serve" || true
      pkill -f "/src/lib/ollama/dist/bin/ollama" || true
      ;;
    web)
      echo "[stop.sh] Stopping web server"
      pkill -f "web/server.sh" || true
      pkill -f "python3.*http.server" || true
      pkill -f "python3.*PORT.*OLLAMA_URL" || true
      ;;
  esac
}

stop_service ollama
stop_service web
