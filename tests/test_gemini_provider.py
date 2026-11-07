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


class _Resp:
    text = '{"ok": true}'


class _FakeModels:
    def __init__(self, busy: set):
        self.busy, self.tried = busy, []

    def generate_content(self, model, contents, config):
        self.tried.append(model)
        if model in self.busy:
            from google.genai import errors
            raise errors.ServerError(503, {"error": {"code": 503, "message": "busy", "status": "UNAVAILABLE"}})
        return _Resp()


def test_busy_model_is_skipped_without_waiting():
    import time

    p = GeminiProvider("fake-key", "lite", "emb", fallback_models="flash")
    fake = _FakeModels(busy={"lite"})
    p.client = type("C", (), {"models": fake})()
    start = time.monotonic()
    assert p.generate_json("hi") == {"ok": True}
    assert fake.tried == ["lite", "flash"]
    assert time.monotonic() - start < 1


def test_all_models_busy_gives_friendly_error():
    import pytest
    from fastapi import HTTPException

    p = GeminiProvider("fake-key", "a", "emb", fallback_models="b")
    p.client = type("C", (), {"models": _FakeModels(busy={"a", "b"})})()
    with pytest.raises(HTTPException) as e:
        p.generate_json("hi")
    assert e.value.status_code == 503
