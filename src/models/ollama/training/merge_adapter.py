#!/usr/bin/env python3
"""Merge LoRA adapter with base model."""
import sys

from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel


def main():
    if len(sys.argv) != 4:
        print(
            f"Usage: {sys.argv[0]} <base_model> <adapter_dir> <output_dir>"
        )
        sys.exit(1)

    base_model_name = sys.argv[1]
    adapter_dir = sys.argv[2]
    output_dir = sys.argv[3]

    print(f"[train] Loading base model {base_model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        trust_remote_code=True,
        torch_dtype="auto",
        device_map="cpu",
    )

    print(f"[train] Loading adapter from {adapter_dir}...")
    model = PeftModel.from_pretrained(model, adapter_dir)

    print("[train] Merging adapter...")
    model = model.merge_and_unload()

    print(f"[train] Saving merged model to {output_dir}...")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)


if __name__ == "__main__":
    main()
