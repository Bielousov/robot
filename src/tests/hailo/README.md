### Usage

Requires `hailo-ollama` running (see `src/lib/hailo/docs/install.txt`) so the model
stays resident between separate script runs instead of reloading each time.

- `HAILO_MODEL=qwen2.5:1.5b python src/tests/hailo/benchmark.py`
