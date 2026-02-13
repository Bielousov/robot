#!/bin/bash

# Get the directory where THIS script lives (./v4/lib/vosk)
LIB_VOSK_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# Define destination paths
DIST_DIR="$LIB_VOSK_DIR/dist"
MODELS_DIR="$LIB_VOSK_DIR/models"

# Path Logic to find .env
PROJECT_ROOT=$(dirname $(dirname "$LIB_VOSK_DIR"))
ENV_FILE="$(dirname "$PROJECT_ROOT")/.env"

# Load Environment Variables (optional: could define VOSK_MODEL_LIST)
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
    VOSK_MODELS=$(echo $VOSK_MODELS | tr -d '\r')
else
    echo "[Warning] .env file not found at $ENV_FILE. Using defaults."
    VOSK_MODELS="vosk-small-en-us-0.15|https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
fi

mkdir -p "$MODELS_DIR"
mkdir -p "$DIST_DIR"

# 1. Install VOSK Python library into the current virtualenv
VOSK_PYTHON="$DIST_DIR/vosk"
if [ ! -d "$VOSK_PYTHON" ]; then
    echo "------------------------------------------------"
    echo "[Engine] Installing VOSK Python library into $DIST_DIR..."
    
    # Install into dist using pip (inside venv)
    pip install --target="$DIST_DIR" vosk
    
    # Optional: create a marker file
    touch "$VOSK_PYTHON/.installed"
else
    echo "[Engine] VOSK Python library exists. Skipping."
fi

# 2. Download Models directly to /models
IFS=";" read -ra MODEL_ENTRIES <<< "$VOSK_MODELS"
for entry in "${MODEL_ENTRIES[@]}"; do
    [ -z "$entry" ] && continue
    IFS="|" read -r MODEL_NAME MODEL_URL <<< "$entry"
    MODEL_DIR="$MODELS_DIR/$MODEL_NAME"
    
    if [ -d "$MODEL_DIR" ]; then
        echo "[Model] $MODEL_NAME exists. Skipping."
        continue
    fi

    echo "------------------------------------------------"
    echo "[Model] Downloading and extracting: $MODEL_NAME"

    TEMP_ZIP="$MODELS_DIR/$MODEL_NAME.zip"
    wget -q --show-progress -L -O "$TEMP_ZIP" "$MODEL_URL"
    
    # Extract into models folder (strip top-level folder)
    unzip -q "$TEMP_ZIP" -d "$MODELS_DIR"
    rm "$TEMP_ZIP"
done

echo "------------------------------------------------"
echo "[Success] VOSK setup complete."
