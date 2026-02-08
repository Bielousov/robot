#!/bin/bash
# .v4/lib/ollama/install.sh

# 1. Use absolute paths that are 100% reliable
OLLAMA_LIB_DIR=$(cd "$(dirname "$0")" && pwd)
PROJECT_ROOT=$(cd "$OLLAMA_LIB_DIR/../.." && pwd)

DIST_DIR="$OLLAMA_LIB_DIR/dist"
MODELS_DIR="$OLLAMA_LIB_DIR/models"
OLLAMA_APP="$DIST_DIR/ollama"
PERSONALITY_MODEL_FILE="$PROJECT_ROOT/pip.modelfile"

# 2. Critical: Ensure the directory exists BEFORE starting the server
mkdir -p "$DIST_DIR"
mkdir -p "$MODELS_DIR"

echo "[Ollama] Starting local server..."
export OLLAMA_MODELS="$MODELS_DIR"
# RPi5 Memory Optimizations
export OLLAMA_CONTEXT_LENGTH=4096
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_NOPRELOAD=1

# Use the full path for the log file to avoid "Permission denied" at root
"$OLLAMA_APP" serve > "$DIST_DIR/server.log" 2>&1 &
OLLAMA_PID=$!

# Wait for server to wake up
echo "[Ollama] Waiting for server (PID: $OLLAMA_PID)..."
sleep 8

# 3. Pull and Create
echo "[Ollama] Pulling Gemma 3 1B..."
"$OLLAMA_APP" pull gemma3:1b

echo "[Ollama] Creating personality 'pip'..."
# 1. Force a RAM clear by hitting the unload endpoint
curl -s -X POST http://localhost:11434/api/generate -d '{"model": "gemma3:1b", "keep_alive": 0}' > /dev/null

if [ -f "$PERSONALITY_MODEL_FILE" ]; then
    # 2. Use the 'create' command with the --quantize flag (if supported) 
    # OR simply ensure no other models are hanging around.
    
    # We use 'create' but we must ensure we aren't asking Ollama to do 
    # anything heavy. 
    "$OLLAMA_APP" create pip -f "$PERSONALITY_MODEL_FILE"
    
    # Check if the create actually worked
    if [ $? -eq 0 ]; then
        echo "[Success] 'pip' model created."
    else
        echo "[Error] Create command failed with exit code $?"
    fi
else
    echo "[Error] Could not find $PERSONALITY_MODEL_FILE"
fi

# 4. Clean shutdown
kill $OLLAMA_PID
echo "[Ollama] Setup complete!"

