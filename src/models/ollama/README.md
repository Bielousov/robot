# Ollama LoRA Personality Model

Train a custom LoRA personality adapter for the Qwen2.5-1.5B model. Two training pipelines optimized for different hardware:

| Approach                 | Hardware                     | Speed        | Best For                          |
| ------------------------ | ---------------------------- | ------------ | --------------------------------- |
| **CPU** (`train.sh`)     | RPi5, servers, any Linux/Mac | ~1 iter/min  | Production inference on RPi5      |
| **GPU** (`train-gpu.sh`) | Mac M1+ (MLX)                | ~100x faster | Fast iteration on Mac development |

Both outputs are identical **Hugging Face format models** ready for Hailo HEF conversion.

## Quick Start

### CPU Training (RPi5, any system)

```bash
./train.sh
```

Outputs merged model to `build/fused/pip/`. PyTorch on CPU, works everywhere.

### GPU Training (Mac M1+ only)

```bash
./train-gpu.sh
```

Same output, **~100x faster** using Apple's MLX framework with GPU acceleration.

**Customizable parameters (both flows):**

```bash
BASE_MODEL=Qwen/Qwen2.5-1.5B-Instruct \
OLLAMA_MODEL_NAME=pip-custom \
TRAIN_ITERS=500 \
BATCH_SIZE=2 \
LEARNING_RATE=1e-4 \
./train.sh
```

### Upload to RPi5

After training on your Mac, upload the merged model to the robot:

```bash
# Copy merged model to RPi5
rsync -avz --progress build/fused/pip/ pip@robot:/home/pip/robot/src/models/ollama/build/fused/pip/

# Or with SSH key authentication
rsync -avz --progress -e "ssh -i ~/.ssh/id_rsa" build/fused/pip/ pip@robot:/home/pip/robot/src/models/ollama/build/fused/pip/
```

**Network tips:**

- Use `-z` to compress during transfer (faster on slower networks)
- Use `--progress` to see transfer speed
- Use `--bwlimit=10000` to limit bandwidth (in KiB/s)

Once uploaded, restart the robot service:

```bash
ssh pip@robot "sudo systemctl restart robot.service"
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

### CPU Training (aarch64 - PyTorch)

| Script                                                                 | Purpose                            |
| ---------------------------------------------------------------------- | ---------------------------------- |
| [train.sh](train.sh)                                                   | Orchestrates CPU training pipeline |
| [training/aarch64/train_adapter.py](training/aarch64/train_adapter.py) | PyTorch LoRA adapter training      |
| [training/aarch64/merge_adapter.py](training/aarch64/merge_adapter.py) | Merge adapter with base model      |

### GPU Training (MLX - Mac M1+)

| Script                                                               | Purpose                            |
| -------------------------------------------------------------------- | ---------------------------------- |
| [train-gpu.sh](train-gpu.sh)                                         | Orchestrates GPU training pipeline |
| [training/darwin/train_adapter.py](training/darwin/train_adapter.py) | MLX LoRA adapter training          |
| [training/darwin/merge_adapter.py](training/darwin/merge_adapter.py) | MLX adapter merge                  |

### Shared

| Script                                               | Purpose                                          |
| ---------------------------------------------------- | ------------------------------------------------ |
| [training/prepare_data.py](training/prepare_data.py) | Split JSONL into train/valid sets (used by both) |

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

## Setup

### CPU Training (PyTorch)

```bash
pip install torch peft transformers datasets huggingface_hub
```

### GPU Training (Mac M1+)

```bash
pip install mlx mlx-lm huggingface_hub
```

## Troubleshooting

**CPU training out of memory?**

- Reduce `BATCH_SIZE` to 1 (default is already minimal)
- Reduce `TRAIN_ITERS` for faster iteration
- Use GPU training on Mac instead

**GPU training not using accelerator?**

- Verify MLX installation: `python -c "import mlx"`
- Check Mac chip: must be Apple Silicon (M1+), not Intel
- Verify `train-gpu.sh` is executable: `chmod +x train-gpu.sh`

**rsync permission denied?**

```bash
# Fix remote directory permissions
ssh pip@robot "mkdir -p /home/pip/robot/src/models/ollama/build/fused && chmod 755 /home/pip/robot/src/models/ollama/build/fused"
```

**Want to use on Hailo?**

1. Upload merged model (HF format) to Hailo-equipped Pi
2. Install Hailo SDK and compiler tools
3. Convert with Hailo's compiler
4. Load with `src/lib/hailo/client.py`
