#!/usr/bin/env python3
"""Train a LoRA adapter on personality data using MLX (Apple GPU)."""
import json
import subprocess
import sys
from pathlib import Path


def load_jsonl(path):
    """Load JSONL file."""
    data = []
    with open(path) as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def main():
    if len(sys.argv) != 7:
        print(
            f"Usage: {sys.argv[0]} <base_model> <data_dir> <adapter_dir> "
            "<train_iters> <batch_size> <learning_rate>"
        )
        sys.exit(1)

    model_name = sys.argv[1]
    data_dir = sys.argv[2]
    adapter_dir = sys.argv[3]
    train_iters = int(sys.argv[4])
    batch_size = int(sys.argv[5])
    learning_rate = float(sys.argv[6])

    print(f"[train] Using MLX to train LoRA adapter...")
    print(f"[train] Base model: {model_name}")

    # Load and validate data
    print("[train] Loading training data...")
    train_data = load_jsonl(f"{data_dir}/train.jsonl")
    valid_data = load_jsonl(f"{data_dir}/valid.jsonl")

    train_texts = [d.get("text", "") for d in train_data if d.get("text", "").strip()]
    valid_texts = [d.get("text", "") for d in valid_data if d.get("text", "").strip()]

    print(f"[train] Datasets: train={len(train_texts)}, valid={len(valid_texts)}")

    # Use mlx_lm CLI for training (more stable than direct API)
    print(f"[train] Training LoRA adapter with MLX for {train_iters} iterations...")

    cmd = [
        sys.executable, "-m", "mlx_lm.tuner.lora",
        "--model", model_name,
        "--data", data_dir,
        "--iters", str(train_iters),
        "--batch-size", str(batch_size),
        "--learning-rate", str(learning_rate),
        "--adapter-file", str(adapter_dir),
    ]

    try:
        result = subprocess.run(cmd, check=True)
        print(f"[train] Adapter saved to {adapter_dir}")
    except subprocess.CalledProcessError as e:
        print(f"[train] Error during MLX training: {e}")
        print(f"[train] Try: mlx_lm.models.download('{model_name}')")
        sys.exit(1)


if __name__ == "__main__":
    main()
