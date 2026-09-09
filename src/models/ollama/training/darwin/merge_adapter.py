#!/usr/bin/env python3
"""Merge LoRA adapter with base model using MLX."""
import subprocess
import sys
from pathlib import Path

def main():
    if len(sys.argv) != 4:
        print(
            f"Usage: {sys.argv[0]} <base_model> <adapter_dir> <output_dir>"
        )
        sys.exit(1)

    base_model_name = sys.argv[1]
    adapter_dir = sys.argv[2]
    output_dir = sys.argv[3]

    print(f"[train] Merging LoRA adapter with {base_model_name} using MLX...")

    # Use mlx_lm CLI to fuse adapter
    cmd = [
        sys.executable, "-m", "mlx_lm", "fuse",
        "--model", base_model_name,
        "--adapter-path", str(adapter_dir),
        "--save-path", str(output_dir),
        "--dequantize",
    ]

    try:
        result = subprocess.run(cmd, check=True)
        print(f"[train] Merged model saved to {output_dir}")
    except subprocess.CalledProcessError as e:
        print(f"[train] Error during MLX fuse: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
