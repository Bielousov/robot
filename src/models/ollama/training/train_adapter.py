#!/usr/bin/env python3
"""Train a LoRA adapter on personality data using PyTorch + PEFT."""
import json
import sys
from pathlib import Path

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    Trainer,
    TrainingArguments,
)
from peft import get_peft_model, LoraConfig
from datasets import Dataset


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

    print(f"[train] Loading model {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        trust_remote_code=True,
        torch_dtype="auto",
        device_map="cpu",
    )

    print("[train] Setting up LoRA config...")
    lora_config = LoraConfig(
        r=8,
        lora_alpha=32,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )

    model = get_peft_model(model, lora_config)

    print("[train] Loading training data...")
    train_data = load_jsonl(f"{data_dir}/train.jsonl")
    valid_data = load_jsonl(f"{data_dir}/valid.jsonl")

    def tokenize_fn(examples):
        output = tokenizer(
            examples["text"],
            truncation=True,
            max_length=512,
            padding="max_length",
            return_tensors="pt",
        )
        return {"input_ids": output["input_ids"], "labels": output["input_ids"]}

    train_dataset = Dataset.from_dict({"text": [d.get("text", "") for d in train_data]})
    valid_dataset = Dataset.from_dict({"text": [d.get("text", "") for d in valid_data]})

    train_dataset = train_dataset.map(tokenize_fn, batched=True, remove_columns=["text"])
    valid_dataset = valid_dataset.map(tokenize_fn, batched=True, remove_columns=["text"])

    training_args = TrainingArguments(
        output_dir=adapter_dir,
        num_train_epochs=1,
        max_steps=train_iters,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        learning_rate=learning_rate,
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=50,
        save_strategy="steps",
        save_steps=50,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=valid_dataset,
    )

    print("[train] Training...")
    trainer.train()

    print(f"[train] Saving adapter to {adapter_dir}...")
    model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)


if __name__ == "__main__":
    main()
