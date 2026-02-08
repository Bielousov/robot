#!/bin/bash
# .v4/lib/ollama/install.sh

OLLAMA_LIB_DIR=$(dirname $(realpath "$0"))
PROJECT_ROOT=$(dirname $(dirname "$OLLAMA_LIB_DIR"))

DIST_DIR="$OLLAMA_LIB_DIR/dist"
MODELS_DIR="$OLLAMA_LIB_DIR/models"
# We update this to point exactly where the binary will end up
OLLAMA_APP="$DIST_DIR/ollama"
PERSONALITY_MODEL_FILE="$PROJECT_ROOT/pip.modelfile"

echo "[Ollama] Starting local server..."
export OLLAMA_MODELS="$MODELS_DIR"
# Use the absolute path to start the server
"$OLLAMA_APP" serve > "$DIST_DIR/server.log" 2>&1 &
OLLAMA_PID=$!

# Wait for server to wake up
sleep 5

echo "[Ollama] Pulling Gemma 3 1B..."
"$OLLAMA_APP" pull gemma3:1b

echo "[Ollama] Creating personality 'pip'..."
if [ -f "$PERSONALITY_MODEL_FILE" ]; then
    "$OLLAMA_APP" create pip -f "$PERSONALITY_MODEL_FILE"
else
    echo "[Error] Could not find $PERSONALITY_MODEL_FILE"
fi

kill $OLLAMA_PID
echo "[Ollama] Setup complete!"