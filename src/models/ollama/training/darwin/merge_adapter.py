#!/usr/bin/env python3
"""Merge LoRA adapter with base model using MLX."""
import json
import os
import sys
from pathlib import Path

import mlx.core as mx
from mlx_lm.utils import load, load_config
from mlx.utils import tree_flatten, tree_unflatten


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

    try:
        # Load model with adapter
        print("[train] Loading model and adapter...")
        model, tokenizer, config = load(
            base_model_name,
            adapter_path=adapter_dir,
            return_config=True,
        )

        # Fuse LoRA layers into the model
        print("[train] Fusing adapter weights into model...")
        fused_linears = [
            (n, m.fuse())
            for n, m in model.named_modules()
            if hasattr(m, "fuse")
        ]

        if fused_linears:
            model.update_modules(tree_unflatten(fused_linears))

        # Save the merged model manually (avoid MLX's save() validation)
        print("[train] Saving merged model...")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save model weights
        model.save_weights(str(output_path / "model.safetensors"))

        # Save config
        if config is not None:
            with open(output_path / "config.json", "w") as f:
                json.dump(config, f, indent=2)

        # Save tokenizer
        if tokenizer is not None:
            tokenizer.save_pretrained(str(output_path))

        print(f"[train] Merged model saved to {output_dir}")

    except Exception as e:
        print(f"[train] Error during MLX merge: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
