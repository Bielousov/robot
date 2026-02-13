#!/bin/bash

# This finds the absolute path to the directory containing THIS script
REAL_PATH=$(realpath "$0")
SCRIPT_DIR=$(dirname "$REAL_PATH")

echo "[Main] Starting Robot v4 Setup..."
echo "[Main] Detected Script Directory: $SCRIPT_DIR"

# Define the installer paths
OLLAMA_INSTALLER="$SCRIPT_DIR/lib/ollama/install.sh"
PIPER_INSTALLER="$SCRIPT_DIR/lib/piper/install.sh"
VOSK_INSTALLER="$SCRIPT_DIR/lib/vosk/install.sh"


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
fi

echo "[Main] Installation sequence finished."

# --- Run Vosk Installer ---
if [ -f "$VOSK_INSTALLER" ]; then
    echo "[Main] Launching Vosk (STT) Installer..."
    chmod +x "$VOSK_INSTALLER"
    bash "$VOSK_INSTALLER"
else
    echo "[Error] Could not find Vosk installer at: $VOSK_INSTALLER"
fi

echo "[Main] Installation sequence finished."