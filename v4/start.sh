#!/bin/bash
# Using #!/bin/bash instead of #!/bin/sh ensures [ "$1" == "stop" ] works.

# 1. Setup paths relative to the script location
PROJECT_ROOT=$(dirname $(realpath "$0"))
OLLAMA_DIR="$PROJECT_ROOT/lib/ollama"
DIST_DIR="$OLLAMA_DIR/dist"
MODELS_DIR="$OLLAMA_DIR/models"
OLLAMA_BIN="$DIST_DIR/ollama"
LOG_FILE="$DIST_DIR/server.log"

# 2. Function to stop the service
stop_brain() {
    if pgrep -f "ollama serve" > /dev/null; then
        echo "[-] Stopping Ollama service..."
        pkill -f "ollama serve"
        sleep 2
    else
        echo "[!] Ollama is not currently running."
    fi
}

# 3. Check for 'stop' argument (using single = for portability)
if [ "$1" = "stop" ]; then
    stop_brain
    exit 0
fi

# 4. Ensure directories exist
mkdir -p "$DIST_DIR"
mkdir -p "$MODELS_DIR"

# 5. Stop existing instances before starting fresh
stop_brain

# 6. Optimization & Context length fixes for RPi5
export OLLAMA_MODELS="$MODELS_DIR"
export OLLAMA_CONTEXT_LENGTH=4096
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_NUM_PARALLEL=1

echo "[Robot] Waking up the brain..."

# 7. Start server
"$OLLAMA_BIN" serve > "$LOG_FILE" 2>&1 &

echo "[Robot] Brain is warming up. Waiting 8 seconds..."
sleep 8

# 8. Health Check
if curl -s http://localhost:11434/api/version > /dev/null; then
    echo "[Robot] Ready for snarky comments."
else
    echo "[Error] Brain failed to start. Check logs at: $LOG_FILE"
fi