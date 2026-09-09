#!/bin/bash

# This finds the absolute path to the directory containing THIS script
REAL_PATH=$(realpath "$0")
SCRIPT_DIR=$(dirname "$REAL_PATH")

echo "[Main] Starting Robot v4 Setup..."
echo "[Main] Detected Script Directory: $SCRIPT_DIR"

# Define the installer paths
OLLAMA_INSTALLER="$SCRIPT_DIR/src/lib/ollama/install.sh"
PIPER_INSTALLER="$SCRIPT_DIR/src/lib/piper/install.sh"
HAILO_INSTALLER="$SCRIPT_DIR/src/lib/hailo/install.sh"
WEB_INSTALLER="$SCRIPT_DIR/web/install.sh"


# --- Run Ollama Installer ---
if [ -f "$OLLAMA_INSTALLER" ]; then
    echo "[Main] Launching Ollama (LLM) Installer..."
    chmod +x "$OLLAMA_INSTALLER"
    bash "$OLLAMA_INSTALLER"
else
    echo "[Error] Could not find Ollama installer at: $OLLAMA_INSTALLER"
    exit 1
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

# --- Run Web Installer ---
# if [ -f "$WEB_INSTALLER" ]; then
#     echo "[Main] Launching Web UI Installer..."
#     chmod +x "$WEB_INSTALLER"
#     bash "$WEB_INSTALLER"
# else
#     echo "[Error] Could not find Web installer at: $WEB_INSTALLER"
# fi

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