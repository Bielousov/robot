import os
import unittest

from models.ollama.identity import build_identity_system_prompt


class IdentityPromptTests(unittest.TestCase):
    def test_lora_disables_system_prompt(self):
        original = os.environ.get("LLM_LORA_PATH")
        try:
            os.environ["LLM_LORA_PATH"] = "/tmp/robot-personality.lora"
            self.assertEqual(build_identity_system_prompt(), "")
        finally:
            if original is None:
                os.environ.pop("LLM_LORA_PATH", None)
            else:
                os.environ["LLM_LORA_PATH"] = original


if __name__ == "__main__":
    unittest.main()
