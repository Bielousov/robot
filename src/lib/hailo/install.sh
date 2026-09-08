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

    WHISPER_MODEL_HEF=$(grep -v '^#' "$ENV_FILE" \
        | grep '^HAILO_WHISPER_MODEL_HEF=' \
        | cut -d '=' -f2 \
        | tr -d '"' \
        | tr -d "'")
fi

HAILO_VERSION=${HAILO_VERSION:-"5.3.0"}
MODEL_HEF=${MODEL_HEF:-"Qwen2.5-1.5B-Instruct.hef"}

install_model() {
    local model_hef="$1"
    local model_file="$MODELS_DIR/$model_hef"
    local model_url="https://dev-public.hailo.ai/v$HAILO_VERSION/blob/$model_hef"

    mkdir -p "$MODELS_DIR"

    if [ -s "$model_file" ]; then
        echo "[Hailo] $model_hef is already installed. Skipping download."
    else
        echo "[Hailo] Installing $model_hef..."
        echo "[Hailo] Version: $HAILO_VERSION"
        echo "[Hailo] Destination: $model_file"

        rm -f "$model_file"

        wget \
            --continue \
            --tries=5 \
            --show-progress \
            "$model_url" \
            -O "$model_file"

        sync
    fi

    if [ ! -s "$model_file" ]; then
        echo "[Hailo] ERROR: $model_file is missing or empty."
        exit 2
    fi

    echo "[Hailo] Model installed:"
    ls -lh "$model_file"

    echo "[Hailo] SHA256:"
    sha256sum "$model_file"
}

install_model "$MODEL_HEF"

if [ -n "$WHISPER_MODEL_HEF" ]; then
    install_model "$WHISPER_MODEL_HEF"
else
    echo "[Hailo] HAILO_WHISPER_MODEL_HEF not set. Skipping Whisper model download."
fi

echo "[Hailo] Done."