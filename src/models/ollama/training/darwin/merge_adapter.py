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
        sys.executable, "-m", "mlx_lm.tuner.fuse",
        "--model", base_model_name,
        "--adapter-file", str(adapter_dir),
        "--save-path", str(output_dir),
        "--dequantize",  # Convert to full precision for broader compatibility
    ]

    try:
        result = subprocess.run(cmd, check=True)
        print(f"[train] Merged model saved to {output_dir}")

        # Create config.json for compatibility
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        config_path = Path(output_dir) / "config.json"
        if not config_path.exists():
            import json
            config = {
                "architectures": ["QwenForCausalLM"],
                "model_type": "qwen",
                "merged_from_lora": True,
            }
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
            print(f"[train] Created config.json at {output_dir}")

    except subprocess.CalledProcessError as e:
        print(f"[train] Error during MLX fuse: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
