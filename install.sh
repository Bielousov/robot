#!/bin/bash

# This finds the absolute path to the directory containing THIS script
REAL_PATH=$(realpath "$0")
SCRIPT_DIR=$(dirname "$REAL_PATH")

echo "[Main] Starting Robot v4 Setup..."
echo "[Main] Detected Script Directory: $SCRIPT_DIR"

# Define the installer paths
OLLAMA_INSTALLER="$SCRIPT_DIR/src/lib/ollama/install.sh"
OLLAMA_MODEL_INSTALLER="$SCRIPT_DIR/src/models/ollama/install.sh"
PIPER_INSTALLER="$SCRIPT_DIR/src/lib/piper/install.sh"
HAILO_INSTALLER="$SCRIPT_DIR/src/lib/hailo/install.sh"


# --- Run Ollama Installer ---
if [ -f "$OLLAMA_INSTALLER" ]; then
    echo "[Main] Launching Ollama (LLM) Installer..."
    chmod +x "$OLLAMA_INSTALLER"
    bash "$OLLAMA_INSTALLER"
else
    echo "[Error] Could not find Ollama installer at: $OLLAMA_INSTALLER"
    exit 1
fi

# --- Run Ollama Personality Model Installer ---
# Non-fatal: a trained model is optional (uploaded separately after running
# src/models/ollama/train.sh elsewhere), so a missing/untrained model should
# not abort the rest of the install - just warn and keep going.
if [ -f "$OLLAMA_MODEL_INSTALLER" ]; then
    echo "[Main] Launching Ollama personality model installer..."
    chmod +x "$OLLAMA_MODEL_INSTALLER"
    if ! bash "$OLLAMA_MODEL_INSTALLER"; then
        echo "[Warning] Personality model not installed - continuing with the base model."
        echo "[Warning] Train one with src/models/ollama/train.sh, upload it, then re-run: $OLLAMA_MODEL_INSTALLER"
    fi
else
    echo "[Warning] Could not find Ollama model installer at: $OLLAMA_MODEL_INSTALLER - skipping."
fi



# --- Run Piper Installer ---
if [ -f "$PIPER_INSTALLER" ]; then
    echo "[Main] Launching Piper (TTS) Installer..."
    chmod +x "$PIPER_INSTALLER"
    bash "$PIPER_INSTALLER"
else
    echo "[Error] Could not find Piper installer at: $PIPER_INSTALLER"
    exit 1
fi

echo "[Main] Installation sequence finished."

# --- Run Hailo Installer (LLM + Whisper STT models) ---
if [ -f "$HAILO_INSTALLER" ]; then
    echo "[Main] Launching Hailo (LLM/STT) Installer..."
    chmod +x "$HAILO_INSTALLER"
    bash "$HAILO_INSTALLER"
else
    echo "[Error] Could not find Hailo installer at: $HAILO_INSTALLER"
fi

# --- Install systemd services ---
ROBOT_SERVICE="$SCRIPT_DIR/system/services/robot.service"
if [ -f "$ROBOT_SERVICE" ]; then
    echo "[Main] Installing robot.service..."
    sudo cp "$ROBOT_SERVICE" /etc/systemd/system/robot.service
    sudo systemctl daemon-reload
    sudo systemctl enable robot.service
    sudo systemctl restart robot.service
else
    echo "[Error] Could not find robot.service at: $ROBOT_SERVICE"
    exit 1
fi

echo "[Main] Installation sequence finished."