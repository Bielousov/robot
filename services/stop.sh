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
    return 0
  fi

  case "$name" in
    ollama)
      echo "[stop.sh] Stopping Ollama API"
      pkill -f "ollama serve" || true
      ;;
    web)
      echo "[stop.sh] Stopping web server"
      pkill -f "web.server.sh" || true
      pkill -f "python3.*http.server" || true
      ;;
  esac
}

stop_service ollama
stop_service web
