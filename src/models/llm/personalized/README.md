# Pip Personality LoRA on Apple Silicon

This guide trains the Qwen2.5-1.5B personality adapter on an Apple Silicon Mac, such as an M1 Max. Training uses Apple's Metal backend through MLX. The Raspberry Pi does not need to train the adapter.

## 1. Create a Mac training environment

Run these commands on the M1 Max, from the repository root:

```bash
python3 -m venv .venv-mlx
source .venv-mlx/bin/activate
python -m pip install --upgrade pip
pip install mlx mlx-lm
```

Check that MLX sees the Apple GPU:

```bash
python -c "import mlx.core as mx; print(mx.default_device())"
```

The output should identify an `gpu` device.

## 2. Download the MLX base model

Use the same Qwen family and size as the robot's Ollama base model:

```bash
hf download \
  mlx-community/Qwen2.5-1.5B-Instruct-4bit \
  --local-dir "$HOME/.cache/mlx-models/Qwen2.5-1.5B-Instruct-4bit"
```

If `hf` is unavailable:

```bash
pip install huggingface_hub
```

Install llama.cpp tools:

```bash
git clone https://github.com/ggerganov/llama.cpp.git "$HOME/src/llama.cpp"
python -m pip install -r "$HOME/src/llama.cpp/requirements.txt"
cd "$HOME/src/llama.cpp"
cmake "$HOME/src/llama.cpp"
```

## 3. Train the adapter

Start with a small run to verify the pipeline:

```bash
python -m mlx_lm lora \
  --model "$HOME/.cache/mlx-models/Qwen2.5-1.5B-Instruct-4bit" \
  --data src/models/llm/personalized/build/data \
  --train \
  --iters 300 \
  --batch-size 1 \
  --num-layers 4 \
  --learning-rate 1e-5 \
  --adapter-path src/models/llm/personalized/build/adapters/pip-qwen2.5
```

For a first run, watch the training and validation loss. Do not increase the number of iterations just to force training loss lower; that can make the robot repeat the training examples instead of generalizing its style.

For a larger dataset, try `--iters 600` and compare responses against a fixed evaluation prompt set.

To run the complete retraining, fusion, GGUF conversion, Q4_K_M quantization,
and Ollama model creation pipeline in one step:

```bash
src/models/llm/personalized/train.sh
```

The script uses `.venv-mlx/bin/python`, `$HOME/src/llama.cpp`, and creates
`pip-personality`. Override paths or settings with environment variables such
as `PYTHON`, `BASE_MODEL`, `LLAMA_CPP_DIR`, `TRAIN_ITERS`, or
`SKIP_OLLAMA=1`.

## 4. Fuse the adapter

Create a standalone fused MLX model for testing:

```bash
python -m mlx_lm.fuse \
  --model "$HOME/.cache/mlx-models/Qwen2.5-1.5B-Instruct-4bit" \
  --adapter-path src/models/llm/personalized/build/adapters/pip-qwen2.5 \
  --save-path src/models/llm/personalized/build/fused/pip-qwen2.5 \
  --dequantize
```

Use `--dequantize` when fusing this quantized MLX base model. Without it,
some MLX versions re-quantize the fused layers and the standalone model can
behave like the original base model. The dequantized fused model uses more
disk and memory, but preserves the adapter weights for conversion and testing.

Test the personality before conversion:

```bash
python -m mlx_lm.generate \
  --model src/models/llm/personalized/build/fused/pip-qwen2.5 \
  --prompt "Who are you?" \
  --max-tokens 32
```

Check at least these prompts:

```text
Who are you? Answer in one short sentence.
The sensor is not responding. What should I check?
Are you certain? Answer briefly.
Explain gravity in one sentence.
```

## 5. Convert for Ollama


Convert the fused model to GGUF:

```bash
python "$HOME/src/llama.cpp/convert_hf_to_gguf.py" \
  src/models/llm/personalized/build/fused/pip-qwen2.5 \
  --outfile src/models/llm/personalized/build/pip-qwen2.5-f16.gguf \
  --outtype f16
```

If the MLX fused directory is not accepted by the converter, export the adapter to a Hugging Face Transformers checkpoint first, then run the converter on that checkpoint. The exact export flags depend on the installed `mlx-lm` version; check:

```bash
python -m mlx_lm.fuse --help
```

Quantize the converted model for Raspberry Pi memory limits, using a quantization type supported by the installed `llama.cpp` build:

```bash
"$HOME/src/llama.cpp/build/bin/llama-quantize" \
  src/models/llm/personalized/build/pip-qwen2.5-f16.gguf \
  src/models/llm/personalized/build/pip-qwen2.5-q4_k_m.gguf \
  Q4_K_M
```

If the quantizer is not built, build `llama.cpp` first or use a release binary.

## 6. Create and test the Ollama model

Create `Modelfile.pip`:

```text
FROM /absolute/path/to/pip-qwen2.5-q4_k_m.gguf

TEMPLATE """{{- if .Messages }}
{{- range .Messages }}
{{- if eq .Role "system" }}<|im_start|>system
{{ .Content }}<|im_end|>
{{- else if eq .Role "user" }}<|im_start|>user
{{ .Content }}<|im_end|>
{{- else if eq .Role "assistant" }}<|im_start|>assistant
{{ .Content }}<|im_end|>
{{- end }}
{{- end }}
{{- end }}<|im_start|>assistant
"""

PARAMETER stop "<|im_end|>"
SYSTEM "You are Pip, an autonomous robot. Reply briefly and directly. Do not describe yourself as Qwen or as an AI assistant."
```

The explicit Qwen template is important because some GGUF conversions do not
retain the chat template. The short `SYSTEM` line is a deployment fallback:
Q4 quantization can weaken a small personality adapter's identity behavior.

Then create and test the model:

```bash
ollama create pip-personality -f Modelfile.pip
ollama run pip-personality
```

A merged GGUF is used here, so no separate `LLM_LORA_PATH` is needed for this deployment:

```env
LLM_ENGINE=ollama
OLLAMA_MODEL=qwen2.5:1.5b
PERSONALIZED_MODEL=
LLM_LORA_PATH=
```

Alternatively, keep the base model and use a compatible GGUF adapter with the application's adapter flow:

```env
LLM_ENGINE=ollama
OLLAMA_MODEL=qwen2.5:1.5b
PERSONALIZED_MODEL=pip-personality
LLM_LORA_PATH=/absolute/path/to/personality-adapter.gguf
```

Do not use both a merged personality model and a separate adapter, or the personality may be applied twice.

## 7. Hailo deployment note

This workflow produces an Ollama model. It does not produce a Hailo `.hef` file. HailoRT loads the compiled HEF directly and does not apply an Ollama GGUF adapter at runtime.

To deploy the personality on Hailo, use the fused Hugging Face model as input to the matching Hailo GenAI conversion/compiler workflow, then copy the resulting HEF to the repository's Hailo model directory and configure:

```env
LLM_ENGINE=hailo
HAILO_MODEL_HEF=pip-qwen2.5-1.5B.hef
LLM_LORA_PATH=
```

The exact compiler command depends on the installed Hailo Dataflow Compiler and model-zoo release. Verify the resulting HEF on the Pi before replacing the original model.

## 8. Keep artifacts out of Git

Adapters, fused checkpoints, and GGUF files can be large. Store them outside the repository or add these paths to `.gitignore`:

```text
src/models/llm/personalized/build/adapters/
src/models/llm/personalized/build/fused/
src/models/llm/personalized/*.gguf
```
