"""Checks the Gemini provider's settings without calling Google (no key, no cost)."""
from app.providers.gemini import GeminiProvider


def test_thinking_level_is_sent():
    p = GeminiProvider("fake-key", "gemini-x", "emb", thinking_level="low")
    cfg = p._config("gemini-x")
    assert cfg.thinking_config.thinking_level.value == "LOW"
    assert cfg.response_mime_type == "application/json"


def test_thinking_can_be_turned_off():
    p = GeminiProvider("fake-key", "gemini-x", "emb", thinking_level="")
    assert p._config("gemini-x").thinking_config is None


def test_fallback_models_are_tried_in_order():
    p = GeminiProvider("fake-key", "main", "emb", fallback_models="b1, b2")
    assert p.chat_models == ["main", "b1", "b2"]
