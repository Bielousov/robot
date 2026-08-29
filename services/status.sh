#!/bin/sh
set -eu

process_running() {
  pattern="$1"
  pgrep -af "$pattern" >/dev/null 2>&1
}

print_status() {
  name="$1"

  if command -v systemctl >/dev/null 2>&1; then
    if systemctl is-active --quiet "${name}.service" 2>/dev/null; then
      echo "[status.sh] ${name}.service: running"
      return 0
    fi
  fi

  case "$name" in
    ollama)
      if process_running "ollama serve" || process_running "/src/lib/ollama/dist/bin/ollama"; then
        echo "[status.sh] ollama: running"
      else
        echo "[status.sh] ollama: stopped"
      fi
      ;;
    web)
      if process_running "web/server.sh" || process_running "python3.*http.server" || process_running "python3.*PORT.*OLLAMA_URL"; then
        echo "[status.sh] web: running"
      else
        echo "[status.sh] web: stopped"
      fi
      ;;
  esac
}

print_status ollama
print_status web
