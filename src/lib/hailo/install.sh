#!/bin/bash
# ./src/lib/hailo/install.sh

set -e

LIB_HAILO_DIR=$(dirname "$(realpath "$0")")
PROJECT_ROOT=$(dirname "$(dirname "$LIB_HAILO_DIR")")
ENV_FILE="$PROJECT_ROOT/../.env"

MODELS_DIR="$LIB_HAILO_DIR/models"

if [ -f "$ENV_FILE" ]; then
    echo "[Hailo] Loading config from $ENV_FILE"

    HAILO_VERSION=$(grep -v '^#' "$ENV_FILE" \
        | grep '^HAILO_VERSION=' \
        | cut -d '=' -f2 \
        | tr -d '"' \
        | tr -d "'")

    MODEL_HEF=$(grep -v '^#' "$ENV_FILE" \
        | grep '^HAILO_MODEL_HEF=' \
        | cut -d '=' -f2 \
        | tr -d '"' \
        | tr -d "'")
fi

HAILO_VERSION=${HAILO_VERSION:-"5.3.0"}
MODEL_HEF=${MODEL_NAME:-"Qwen2.5-1.5B-Instruct.hef"}

MODEL_FILE="$MODELS_DIR/$MODEL_HEF"
MODEL_URL="https://dev-public.hailo.ai/v$HAILO_VERSION/blob/$MODEL_HEF"

mkdir -p "$MODELS_DIR"

if [ -s "$MODEL_FILE" ]; then
    echo "[Hailo] $MODEL_HEF is already installed. Skipping download."
else
    echo "[Hailo] Installing $MODEL_HEF..."
    echo "[Hailo] Version: $HAILO_VERSION"
    echo "[Hailo] Destination: $MODEL_FILE"

    rm -f "$MODEL_FILE"

    wget \
        --continue \
        --tries=5 \
        --show-progress \
        "$MODEL_URL" \
        -O "$MODEL_FILE"

    sync
fi

if [ ! -s "$MODEL_FILE" ]; then
    echo "[Hailo] ERROR: $MODEL_FILE is missing or empty."
    exit 2
fi

echo "[Hailo] Model installed:"
ls -lh "$MODEL_FILE"

echo "[Hailo] SHA256:"
sha256sum "$MODEL_FILE"

echo "[Hailo] Done."