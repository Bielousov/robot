#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

if ! command -v sudo >/dev/null 2>&1; then
  echo "[install.sh] sudo is required to install the systemd units."
  exit 1
fi

for unit in ollama.service web.service; do
  src="$SCRIPT_DIR/$unit"
  dst="/etc/systemd/system/$unit"

  if [ ! -f "$src" ]; then
    echo "[install.sh] Missing unit file: $src"
    exit 1
  fi

  echo "[install.sh] Installing $unit -> $dst"
  sudo cp "$src" "$dst"
done

sudo systemctl daemon-reload
sudo systemctl enable --now ollama.service
sudo systemctl enable --now web.service

echo "[install.sh] Service installation complete."
