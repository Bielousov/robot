# Ollama LoRA Personality Model

Train a custom LoRA personality adapter for the Qwen2.5-1.5B model. One script, auto-detected backend:

| Backend           | Hardware                        | Speed        | Auto-Selected When             |
| ----------------- | ------------------------------- | ------------ | ------------------------------ |
| **GPU** (MLX)     | Mac (Apple Silicon)             | ~100x faster | macOS detected + MLX installed |
| **CPU** (PyTorch) | Any (RPi5, servers, Linux, Mac) | ~1 iter/min  | Default / no MLX               |

Single script handles both. Outputs are identical **Hugging Face format models** ready for Hailo HEF conversion.

## Quick Start

```bash
./train.sh
```

That's it. The script auto-detects your platform:

- **Apple Soilicon Mac with MLX**: Uses GPU training (fast)
- **Everywhere else**: Uses PyTorch CPU training (universal)

Outputs the final portable Ollama model store to `build/pip/` (training
intermediates - data split, adapter, fused model, Modelfile - live separately
under `training/build/`, wiped at the start of every run).

**Customizable parameters:**

```bash
BASE_MODEL=Qwen/Qwen2.5-1.5B-Instruct \
OLLAMA_MODEL_NAME=pip-custom \
TRAIN_ITERS=500 \
BATCH_SIZE=2 \
LEARNING_RATE=1e-4 \
./train.sh
```

### Upload to RPi5

`train.sh` runs `ollama create` locally against an isolated, disposable Ollama
server (a fresh `OLLAMA_MODELS` directory on a non-default port, so it never
touches your regular Ollama setup) and prints the resulting portable model
store's path: `build/pip/`. That directory *is* the model as Ollama itself
stores it - content-addressed blobs plus a manifest, no absolute paths - so
there's no conversion step needed on the robot, just uploading it and
registering it in place:

```bash
# 1. Upload the model store
rsync -avz --progress build/pip/ pip@pip.local:/home/pip/robot/src/models/ollama/build/pip/

# Or with SSH key authentication
rsync -avz --progress -e "ssh -i ~/.ssh/id_rsa" build/pip/ pip@pip.local:/home/pip/robot/src/models/ollama/build/pip/

# 2. Register it - verifies the blobs/manifest, then merges them into the
#    robot's Ollama models directory (no `ollama create`, no Ollama binary
#    needed on the robot for this step)
ssh pip@pip.local "/home/pip/robot/src/models/ollama/install.sh pip"

# 3. Restart the robot service - its own `ollama serve` (started with
#    OLLAMA_MODELS pointed at that same directory) will find the model
ssh pip@pip.local "sudo systemctl restart robot.service"
```

**If Ollama isn't installed on the training machine**, `train.sh` skips this
and falls back to printing instructions for uploading the raw fused model and
converting it directly on the target machine instead (regenerating the
Modelfile there, then running `ollama create` - see the script's own printed
instructions for that path). [install.sh](install.sh) only *registers* an
already-converted store (see below) - it doesn't run `ollama create`, so it
isn't part of this fallback.

**Network tips:**

- Use `-z` to compress during transfer (faster on slower networks)
- Use `--progress` to see transfer speed
- Use `--bwlimit=10000` to limit bandwidth (in KiB/s)

### Running with Ollama (CPU Fallback)

Once trained, use the merged model with Ollama:

```bash
# Import the merged model into Ollama
ollama create pip-qwen2.5-1.5b -f training/build/Modelfile

# Chat with it
ollama run pip-qwen2.5-1.5b "Hello, who are you?"

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

### Main Entry Point

| Script                   | Purpose                                                                                                                        |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| [train.sh](train.sh)     | Auto-detects platform and runs appropriate backend (GPU on Apple Silicon Macs, CPU else)                                       |
| [install.sh](install.sh) | Run on the target machine after uploading `build/$MODEL_NAME/` - registers the pre-converted model blobs into the robot's Ollama models directory (no `ollama create`, no Ollama binary needed) |

### CPU Training Backend (PyTorch - aarch64)

| Script                                                                 | Purpose                       |
| ---------------------------------------------------------------------- | ----------------------------- |
| [training/aarch64/train_adapter.py](training/aarch64/train_adapter.py) | PyTorch LoRA adapter training |
| [training/aarch64/merge_adapter.py](training/aarch64/merge_adapter.py) | Merge adapter with base model |

### GPU Training Backend (MLX - darwin/MacOS)

| Script                                                               | Purpose                   |
| -------------------------------------------------------------------- | ------------------------- |
| [training/darwin/train_adapter.py](training/darwin/train_adapter.py) | MLX LoRA adapter training |
| [training/darwin/merge_adapter.py](training/darwin/merge_adapter.py) | MLX adapter merge         |

### Shared

| Script                                               | Purpose                      |
| ---------------------------------------------------- | ---------------------------- |
| [training/prepare_data.py](training/prepare_data.py) | Split JSONL into train/valid |

## Output Structure

```
training/build/                   # Training intermediates - wiped at the start of every train.sh run
├── data/                         # Train/validation split (from training/personality.jsonl)
│   ├── train.jsonl
│   └── valid.jsonl
├── adapters/                     # LoRA adapter weights
│   ├── adapter_config.json
│   └── adapter_model.safetensors
├── fused/                        # Merged model (Hugging Face format, ready for Hailo too)
│   ├── config.json
│   ├── model.safetensors
│   ├── tokenizer.json
│   └── tokenizer_config.json
├── Modelfile                     # Ollama Modelfile (FROM ./fused, absolute path)
└── ollama-serve.log

build/
└── pip-qwen2.5/                # Final deliverable - this is what gets uploaded, not wiped between runs
    ├── blobs/                   # Content-addressed (sha256-<hash>), no machine-specific paths
    └── manifests/registry.ollama.ai/library/pip-qwen2.5/latest
```

## Configuration

Edit `training/personality.jsonl` to customize the personality. Each line is a JSON object:

```json
{"text": "I am Pip, a friendly robot. I love helping people."}
{"text": "I prefer brief, direct answers over long explanations."}
```

**Training parameters** (in `train-cpu.sh` and `train-gpu.sh`):

- `TRAIN_ITERS` — number of training steps (default: 300)
- `BATCH_SIZE` — batch size per device (default: 1, increase if OOM allows)
- `LEARNING_RATE` — optimizer learning rate (default: 1e-5)

## Setup

### CPU Training (PyTorch)

```bash
pip install torch peft transformers datasets huggingface_hub
```

### GPU Training (Mac GPU)

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
- Check Mac chip: must be Apple Silicon
- Verify `train-gpu.sh` is executable: `chmod +x train-gpu.sh`

**Want to use on Hailo?**

1. Upload merged model (HF format) to Hailo-equipped Pi
2. Install Hailo SDK and compiler tools
3. Convert with Hailo's compiler
4. Load with `src/lib/hailo/client.py`
