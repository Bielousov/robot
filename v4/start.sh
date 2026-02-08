#!/bin/bash
# Get the absolute path of the project root
PROJECT_ROOT=$(dirname $(realpath "$0"))

# Set model path
export OLLAMA_MODELS="$PROJECT_ROOT/lib/ollama/models"

echo "[Robot] Waking up the brain..."
# Start server and hide the wall of text logs
"$PROJECT_ROOT/lib/ollama/dist/ollama" serve > "$PROJECT_ROOT/lib/ollama/dist/server.log" 2>&1 &

echo "[Robot] Brain is warming up. Waiting 5 seconds..."
sleep 5
echo "[Robot] Ready for snarky comments."