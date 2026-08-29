#!/bin/sh
set -eu

print_status() {
  name="$1"

  if command -v systemctl >/dev/null 2>&1; then
    if systemctl is-active --quiet "${name}.service" 2>/dev/null; then
      echo "[status.sh] ${name}.service: running"
    else
      echo "[status.sh] ${name}.service: stopped"
    fi
    return 0
  fi

  case "$name" in
    ollama)
      if pgrep -f "ollama serve" >/dev/null 2>&1; then
        echo "[status.sh] ollama: running"
      else
        echo "[status.sh] ollama: stopped"
      fi
      ;;
    web)
      if pgrep -f "web/server.sh" >/dev/null 2>&1 || pgrep -f "python3.*http.server" >/dev/null 2>&1; then
        echo "[status.sh] web: running"
      else
        echo "[status.sh] web: stopped"
      fi
      ;;
  esac
}

print_status ollama
print_status web
