import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from lib.ollama.client import OllamaClient


class LoraClientTests(unittest.TestCase):
    @patch("lib.ollama.client.ollama.Client")
    def test_ollama_binds_derived_model_to_adapter(self, client_type):
        client = client_type.return_value
        client.ps.return_value = {}

        with tempfile.NamedTemporaryFile() as adapter:
            ollama_client = OllamaClient(
                host="http://localhost:11434",
                lora_path=adapter.name,
            )
            ollama_client.load_model("qwen2.5:1.5b")

        client.pull.assert_called_once_with("qwen2.5:1.5b")
        client.create.assert_called_once()
        create_kwargs = client.create.call_args.kwargs
        self.assertEqual(create_kwargs["from_"], "qwen2.5:1.5b")
        self.assertEqual(len(create_kwargs["adapters"]), 1)
        self.assertEqual(ollama_client.model, create_kwargs["model"])

    @patch("lib.ollama.client.ollama.Client")
    def test_missing_ollama_adapter_fails_before_create(self, client_type):
        client = client_type.return_value
        client.ps.return_value = {}
        ollama_client = OllamaClient(
            lora_path=Path("/tmp/missing-robot-personality.lora")
        )

        with self.assertRaises(FileNotFoundError):
            ollama_client.load_model("qwen2.5:1.5b")

        client.create.assert_not_called()


if __name__ == "__main__":
    unittest.main()
