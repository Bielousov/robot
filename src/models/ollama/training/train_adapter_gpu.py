#!/usr/bin/env python3
"""Train a LoRA adapter on personality data using MLX (Apple GPU)."""
import json
import sys
from pathlib import Path

import mlx.core as mx
from mlx_lm.lora import linear_to_lora_layers
from mlx_lm.models.utils import load_model, load_tokenizer
from mlx_lm.tuner.custom_sgd import SGD
from mlx_lm.tuner.utils import prepare_data


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

    print(f"[train] Loading model {model_name} with MLX...")
    try:
        model, tokenizer = load_model(model_name)
    except Exception as e:
        print(f"[train] Error loading model: {e}")
        print(f"[train] Ensure model is in MLX format or download with:")
        print(f"[train]   mlx_lm.models.download('{model_name}')")
        sys.exit(1)

    print("[train] Converting to LoRA layers...")
    model = linear_to_lora_layers(model, lora_layers=16, lora_parameters={"lora_rank": 8})

    print("[train] Loading training data...")
    train_data = load_jsonl(f"{data_dir}/train.jsonl")
    valid_data = load_jsonl(f"{data_dir}/valid.jsonl")

    # Extract text from JSONL
    train_texts = [d.get("text", "") for d in train_data if d.get("text", "").strip()]
    valid_texts = [d.get("text", "") for d in valid_data if d.get("text", "").strip()]

    print(f"[train] Preparing datasets (train={len(train_texts)}, valid={len(valid_texts)})")
    train_dataset = prepare_data(
        dataset=train_texts,
        tokenizer=tokenizer,
        max_seq_length=512,
        num_samples=len(train_texts),
    )
    valid_dataset = prepare_data(
        dataset=valid_texts,
        tokenizer=tokenizer,
        max_seq_length=512,
        num_samples=len(valid_texts),
    )

    print("[train] Setting up optimizer...")
    optimizer = SGD(learning_rate=learning_rate)

    print(f"[train] Training for {train_iters} steps...")
    losses = []
    for step in range(train_iters):
        for batch in train_dataset:
            logits = model(batch["input_ids"])
            loss = mx.mean(
                mx.nn.losses.cross_entropy(
                    logits.reshape(-1, logits.shape[-1]),
                    batch["labels"].reshape(-1),
                )
            )
            optimizer.update(model, grads=mx.grad(loss))
            losses.append(loss.item())

        if (step + 1) % 10 == 0:
            avg_loss = sum(losses[-10:]) / 10
            print(f"[train] Step {step + 1}/{train_iters}, loss: {avg_loss:.4f}")

    print(f"[train] Saving adapter to {adapter_dir}...")
    model.save_lora(str(adapter_dir))


if __name__ == "__main__":
    main()
