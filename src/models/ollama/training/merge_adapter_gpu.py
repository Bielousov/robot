#!/usr/bin/env python3
"""Merge LoRA adapter with base model using MLX."""
import sys

import mlx.core as mx
from mlx_lm.models.utils import load_model, load_tokenizer


def main():
    if len(sys.argv) != 4:
        print(
            f"Usage: {sys.argv[0]} <base_model> <adapter_dir> <output_dir>"
        )
        sys.exit(1)

    base_model_name = sys.argv[1]
    adapter_dir = sys.argv[2]
    output_dir = sys.argv[3]

    print(f"[train] Loading base model {base_model_name} with MLX...")
    try:
        model, tokenizer = load_model(base_model_name)
    except Exception as e:
        print(f"[train] Error loading model: {e}")
        sys.exit(1)

    print(f"[train] Loading adapter from {adapter_dir}...")
    try:
        model.load_lora(str(adapter_dir))
    except Exception as e:
        print(f"[train] Error loading adapter: {e}")
        sys.exit(1)

    print("[train] Merging adapter into base model...")
    model = model.merge_lora()

    print(f"[train] Converting to Hugging Face format and saving to {output_dir}...")
    try:
        # Save in HuggingFace format for compatibility
        model.save_pretrained(output_dir)
        tokenizer.save_pretrained(output_dir)
    except AttributeError:
        # MLX model doesn't have save_pretrained, use MLX's native save
        mx.save_safetensors(output_dir, model.parameters())
        print(f"[train] Saved MLX model weights to {output_dir}")
        # Also save tokenizer config for HF compatibility
        import json
        tokenizer_config = {
            "bos_token": tokenizer.bos_token,
            "eos_token": tokenizer.eos_token,
            "pad_token": tokenizer.pad_token,
        }
        with open(f"{output_dir}/tokenizer_config.json", "w") as f:
            json.dump(tokenizer_config, f, indent=2)


if __name__ == "__main__":
    main()
