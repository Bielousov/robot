### Usage

These scripts always run the trained/personality model (see
`src/models/ollama/train.sh`), registered under `OLLAMA_MODEL_NAME` in
`.env` - there is no base-model fallback.

- `OLLAMA_MODEL_NAME=pip python src/tests/ollama/benchmark.py`
