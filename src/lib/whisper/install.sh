#!/bin/bash

# Get the directory where THIS script lives (./src/lib/whisper)
WHISPER_LIB_DIR=$(dirname $(realpath "$0"))
PROJECT_ROOT=$(dirname $(dirname "$WHISPER_LIB_DIR"))
ENV_FILE="$PROJECT_ROOT/../.env"

# Define destination paths
DIST_DIR="$WHISPER_LIB_DIR/dist"
MODELS_DIR="$WHISPER_LIB_DIR/models"
WHISPER_BIN="$DIST_DIR/build/bin/whisper-cli"

# Load Environment Variables
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
    WHISPER_MODEL_NAME="${WHISPER_MODEL_NAME%$'\r'}"
    WHISPER_REPO_URL="${WHISPER_REPO_URL%$'\r'}"
else
    echo "[Fatal] .env file not found at $ENV_FILE"
    exit 1
fi

# Set defaults if not in .env
WHISPER_MODEL_NAME="${WHISPER_MODEL_NAME:-base.en}"
WHISPER_REPO_URL="${WHISPER_REPO_URL:-https://github.com/ggerganov/whisper.cpp.git}"
WHISPER_SAMPLE_RATE="${WHISPER_SAMPLE_RATE:-16000}"

mkdir -p "$DIST_DIR"
mkdir -p "$MODELS_DIR"

# 1. Clone and build whisper.cpp
if [ ! -d "$WHISPER_BIN" ]; then
    echo "------------------------------------------------"
    echo "[Engine] Installing whisper.cpp from $WHISPER_REPO_URL..."
    
    # Ensure build dependencies
    echo "[Deps] Installing build tools (cmake, build-essential)..."
    sudo apt-get update
    if ! sudo apt-get install -y cmake build-essential git; then
        echo "[Error] Failed to install build dependencies"
        exit 1
    fi
    
    # Verify cmake is available
    if ! command -v cmake &> /dev/null; then
        echo "[Error] cmake is not available after installation"
        exit 1
    fi
    
    # Clone the repository
    git clone "$WHISPER_REPO_URL" "$DIST_DIR"
    
    # Build whisper.cpp
    cd "$DIST_DIR"
    echo "[Build] Compiling whisper.cpp..."
    if ! make; then
        echo "[Error] Build failed"
        exit 1
    fi
else
    echo "[Engine] whisper.cpp exists. Skipping."
fi

# 2. Download Model
MODEL_FILE="$MODELS_DIR/${WHISPER_MODEL_NAME}.bin"

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
    if [ -f "models/ggml-${WHISPER_MODEL_NAME}.bin" ]; then
        cp "models/ggml-${WHISPER_MODEL_NAME}.bin" "$MODEL_FILE"
        echo "[Model] Model copied to $MODEL_FILE"
    else
        echo "[Error] Failed to download model"
        exit 1
    fi
    
    cd - > /dev/null
fi

echo "------------------------------------------------"
echo "[Success] Whisper setup complete."
echo "[Info] Binary: $WHISPER_BIN"
echo "[Info] Model: $MODEL_FILE"
echo "[Info] Sample Rate: $WHISPER_SAMPLE_RATE"
