# Ollama LoRA Personality Model

Train a custom LoRA personality adapter for the Qwen2.5-1.5B model using PyTorch + PEFT, optimized for Hailo HEF conversion and CPU fallback via Ollama.

## Quick Start

### Training

```bash
./train.sh
```

Outputs a merged Hugging Face model ready for Hailo conversion at `build/fused/pip-qwen2.5/`.

**Customizable parameters:**
```bash
BASE_MODEL=Qwen/Qwen2.5-1.5B-Instruct \
TRAIN_ITERS=500 \
BATCH_SIZE=2 \
LEARNING_RATE=1e-4 \
./train.sh
```

### Running with Ollama (CPU Fallback)

Once trained, use the merged model with Ollama:

```bash
# Import the merged model into Ollama
ollama create pip-personality -f training/Modelfile.pip

# Chat with it
ollama run pip-personality "Hello, who are you?"

# In Python (same as production)
from lib.ollama.client import OllamaClient

client = OllamaClient()
response = client.chat(
    messages=[{"role": "user", "content": "Hello!"}],
    stream=True,
)
for chunk in response:
    print(chunk["message"]["content"], end="", flush=True)
```

## Pipeline

1. **Prepare data** → Split `training/personality.jsonl` into train/validation (80/20)
2. **Train adapter** → LoRA fine-tuning on Qwen2.5-1.5B with PyTorch
3. **Merge** → Fuse adapter into base model, save as Hugging Face format
4. **Deploy** → Convert to Hailo HEF (for accelerated inference) or use on CPU via Ollama

## Training Scripts

| Script | Purpose |
|--------|---------|
| [train.sh](train.sh) | Orchestrates the full pipeline |
| [training/prepare_data.py](training/prepare_data.py) | Split JSONL into train/valid sets |
| [training/train_adapter.py](training/training/train_adapter.py) | LoRA adapter training |
| [training/merge_adapter.py](training/merge_adapter.py) | Merge adapter with base model |

## Output Structure

```
build/
├── adapters/pip-qwen2.5/       # LoRA adapter weights (intermediate)
│   ├── adapter_config.json
│   └── adapter_model.safetensors
└── fused/pip-qwen2.5/           # Merged model (final output for Hailo)
    ├── config.json
    ├── model.safetensors
    ├── tokenizer.json
    └── tokenizer_config.json
```

## Configuration

Edit `training/personality.jsonl` to customize the personality. Each line is a JSON object:

```json
{"text": "I am Pip, a friendly robot. I love helping people."}
{"text": "I prefer brief, direct answers over long explanations."}
```

**Training parameters** (in `train.sh`):
- `TRAIN_ITERS` — number of training steps (default: 300)
- `BATCH_SIZE` — batch size per device (default: 1, increase if OOM allows)
- `LEARNING_RATE` — optimizer learning rate (default: 1e-5)

## Troubleshooting

**Out of memory?**
- Reduce `BATCH_SIZE` to 1 (default is already minimal)
- Reduce `TRAIN_ITERS` for faster iteration

**Missing dependencies?**
```bash
pip install torch peft transformers datasets
```

**Want to use on Hailo?**
1. Install Hailo SDK and compiler tools
2. Convert merged model to `.hef`:
   ```bash
   hailo_model_zoo convert --model qwen2.5-1.5b --output-path build/fused/pip-qwen2.5/
   ```
3. Load with `src/lib/hailo/client.py`
