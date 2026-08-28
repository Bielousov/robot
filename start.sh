#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

if [ -f "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a
fi

case "${1:-web}" in
  ollama)
    echo "[start.sh] Starting Ollama API without preloading any model"
    exec "$PROJECT_ROOT/src/lib/ollama/dist/bin/ollama" serve
    ;;
  web)
    echo "[start.sh] Starting web server"
    exec bash "$PROJECT_ROOT/services/web.server.sh" "${PORT:-8000}"
    ;;
  *)
    echo "[start.sh] Unknown target: $1"
    echo "Usage: $0 [web|ollama]"
    exit 1
    ;;
esac
