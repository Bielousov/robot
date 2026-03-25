#!/bin/bash

# Get the directory where THIS script lives (./src/lib/whisper)
WHISPER_LIB_DIR=$(dirname $(realpath "$0"))
PROJECT_ROOT=$(dirname $(dirname "$WHISPER_LIB_DIR"))
ENV_FILE="$PROJECT_ROOT/../.env"

# Define destination paths
MODELS_DIR="$WHISPER_LIB_DIR/models"

WHISPER_MODEL_NAME="${WHISPER_MODEL_NAME:-base.en}"
MODEL_FILE_NAME="${WHISPER_MODEL_NAME}.bin"
MODEL_FILE="$MODELS_DIR/$MODEL_FILE_NAME"

# Model download URLs (whisper.cpp models)
declare -A MODEL_URLS=(
    ["tiny.en"]="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin"
    ["base.en"]="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin"
    ["small.en"]="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin"
)

# Load Environment Variables
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
    WHISPER_MODEL_NAME="${WHISPER_MODEL_NAME%$'\r'}"
else
    echo "[Info] .env file not found, using default: $WHISPER_MODEL_NAME"
fi

mkdir -p "$MODELS_DIR"

if [ -f "$MODEL_FILE" ]; then
    echo "[Model] $WHISPER_MODEL_NAME model exists at $MODEL_FILE"
else
    echo "[Info] Downloading $WHISPER_MODEL_NAME model..."
    
    # Get download URL
    MODEL_URL="${MODEL_URLS[$WHISPER_MODEL_NAME]}"
    
    if [ -z "$MODEL_URL" ]; then
        echo "[Error] Unknown model: $WHISPER_MODEL_NAME"
        echo "[Info] Available models: ${!MODEL_URLS[@]}"
        exit 1
    fi
    
    # Download using curl with progress
    if command -v curl &> /dev/null; then
        curl -L --progress-bar -o "$MODEL_FILE" "$MODEL_URL"
    elif command -v wget &> /dev/null; then
        wget -O "$MODEL_FILE" "$MODEL_URL"
    else
        echo "[Error] curl or wget not found. Install one of them."
        exit 1
    fi
    
    if [ -f "$MODEL_FILE" ]; then
        echo "[Success] Model downloaded to $MODEL_FILE"
    else
        echo "[Error] Failed to download model from $MODEL_URL"
        exit 1
    fi
fi

echo "------------------------------------------------"
echo "[Success] Whisper model setup complete."
echo "[Info] Model: $MODEL_FILE"
