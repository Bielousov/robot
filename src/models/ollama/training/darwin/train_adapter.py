#!/usr/bin/env python3
"""Train a LoRA adapter on personality data using MLX (Apple GPU)."""
import subprocess
import sys
from pathlib import Path


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

    # Verify data files exist
    print("[train] Loading training data...")
    train_file = Path(data_dir) / "build" / "train.jsonl"
    valid_file = Path(data_dir) / "build" / "valid.jsonl"

    if not train_file.exists():
        print(f"[train] ERROR: Training data not found at {train_file}")
        sys.exit(1)

    if not valid_file.exists():
        print(f"[train] ERROR: Validation data not found at {valid_file}")
        sys.exit(1)

    # Count samples
    train_count = sum(1 for _ in train_file.open())
    valid_count = sum(1 for _ in valid_file.open())
    print(f"[train] Datasets: train={train_count}, valid={valid_count}")

    # Use mlx_lm CLI for training (more stable than direct API)
    print(f"[train] Training LoRA adapter with MLX for {train_iters} iterations...")

    cmd = [
        sys.executable, "-m", "mlx_lm", "lora",
        "--model", model_name,
        "--data", data_dir,
        "--train",
        "--iters", str(train_iters),
        "--batch-size", str(batch_size),
        "--learning-rate", str(learning_rate),
        "--adapter-path", str(adapter_dir),
    ]
    try:
        result = subprocess.run(cmd, check=True)
        print(f"[train] Adapter saved to {adapter_dir}")

        # Check what files were actually created
        adapter_path = Path(adapter_dir)
        if adapter_path.exists():
            files = list(adapter_path.rglob("*"))
            print(f"[train] Files in adapter_dir: {[f.name for f in files if f.is_file()]}")
        else:
            print(f"[train] Adapter directory does not exist: {adapter_dir}")
    except subprocess.CalledProcessError as e:
        print(f"[train] Error during MLX training: {e}")
        print(f"[train] Try: mlx_lm.models.download('{model_name}')")
        sys.exit(1)


if __name__ == "__main__":
    main()
