#!/bin/bash

# Get the directory where THIS script lives (./src/lib/whisper)
WHISPER_LIB_DIR=$(dirname $(realpath "$0"))
PROJECT_ROOT=$(dirname $(dirname "$WHISPER_LIB_DIR"))
ENV_FILE="$PROJECT_ROOT/../.env"

# Define destination paths
MODELS_DIR="$WHISPER_LIB_DIR/models"

WHISPER_MODEL_NAME="${WHISPER_MODEL_NAME:-small.en}"
MODEL_FILE_NAME="ggml-${WHISPER_MODEL_NAME}.bin"
MODEL_FILE="$MODELS_DIR/$MODEL_FILE_NAME"


# Load Environment Variables
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
    WHISPER_MODEL_NAME="${WHISPER_MODEL_NAME%$'\r'}"
else
    echo "[Fatal] .env file not found at $ENV_FILE"
    exit 1
fi

mkdir -p "$MODELS_DIR"

if [ -f "$MODEL_FILE" ]; then
    echo "[Model] $WHISPER_MODEL_NAME model exists. Skipping."
else
    echo "Model file $MODEL_FILE not found..."

    # Ensure dependencies
    sudo apt-get update && sudo apt-get install -y curl wget

    echo "------------------------------------------------"
    echo "[Model] Downloading: $WHISPER_MODEL_NAME"

    # Download model using whisper.cpp's download script
    cd "$DIST_DIR"
    ./models/download-ggml-model.sh "$WHISPER_MODEL_NAME"
    
    # Copy model to our models directory
    if [ -f "models/${MODEL_FILE_NAME}" ]; then
        cp "models/${WHISPER_MODEL_NAME}" "$MODEL_FILE"
        echo "[Model] Model copied to $MODEL_FILE"
    else
        echo "[Error] Failed to download model"
        exit 1
    fi
    
    cd - > /dev/null
fi

echo "------------------------------------------------"
echo "[Success] Whisper model setup complete."
echo "[Info] Model: $MODEL_FILE"
