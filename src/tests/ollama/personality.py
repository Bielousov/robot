import os

from models.personality import build_personality_system_prompt


def test_build_personality_system_prompt_includes_identity(monkeypatch):
    monkeypatch.setenv("NAME", "Pip")
    monkeypatch.setenv("USER_NAME", "Anton")
    monkeypatch.setenv("ROBOT_ROLE", "autonomous mechanical robot")
    monkeypatch.setenv("CONTEXT_LOCATION", "Vancouver Island, Canada")
    monkeypatch.setenv("LANGUAGE", "English")
    monkeypatch.setenv("OLLAMA_SYSTEM_PROMPT", "You are an autonomous mechanical robot.")

    prompt = build_personality_system_prompt()

    assert "IDENTITY [MANDATORY]" in prompt
    assert "You are Pip." in prompt
    assert "Human operator: Anton" in prompt
    assert "SYSTEM INSTRUCTIONS:" in prompt
    assert "You are an autonomous mechanical robot." in prompt
