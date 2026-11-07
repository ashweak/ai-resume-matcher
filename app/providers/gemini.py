import json
import logging
import time

import httpx
from fastapi import HTTPException
from google import genai
from google.genai import errors, types

from app.providers.base import AIProvider

log = logging.getLogger("uvicorn.error")
BUSY = "The AI is busy right now. Please try again in a minute."


class GeminiProvider(AIProvider):
    """Speed strategy: one quick attempt per model, then move on to the next model.
    (Waiting and retrying a busy model is what made requests take 30+ seconds.)"""

    def __init__(
        self,
        api_key: str,
        chat_model: str,
        embed_model: str,
        fallback_models: str = "",
        thinking_level: str = "low",
        timeout_seconds: int = 20,
    ):
        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=timeout_seconds * 1000,
                retry_options=types.HttpRetryOptions(attempts=1),  # turn off the SDK's own slow retries
            ),
        )
        backups = [m.strip() for m in fallback_models.split(",") if m.strip()]
        self.chat_models = [chat_model, *[m for m in backups if m != chat_model]]
        self.embed_model = embed_model
        self.thinking_level = thinking_level.strip().upper()
        self.no_thinking_cfg: set[str] = set()  # models that rejected thinking_level

    def _config(self, model: str) -> types.GenerateContentConfig:
        thinking = None
        if self.thinking_level and model not in self.no_thinking_cfg:
            thinking = types.ThinkingConfig(thinking_level=self.thinking_level)
        return types.GenerateContentConfig(response_mime_type="application/json", thinking_config=thinking)

    def generate_json(self, prompt: str) -> dict:
        for model in self.chat_models:
            for _ in range(2):  # 2nd try only for: bad JSON, or model doesn't support thinking_level
                start = time.monotonic()
                try:
                    resp = self.client.models.generate_content(model=model, contents=prompt, config=self._config(model))
                    result = json.loads(resp.text)
                    log.info("AI answer from %s in %.1fs", model, time.monotonic() - start)
                    return result
                except json.JSONDecodeError:
                    continue
                except errors.ClientError as e:
                    if e.code == 400 and "think" in str(e).lower() and model not in self.no_thinking_cfg:
                        self.no_thinking_cfg.add(model)
                        continue
                    if e.code in (404, 429):  # unavailable or over quota -> next model
                        log.warning("%s unavailable (%s), trying next model", model, e.code)
                        break
                    raise
                except (errors.ServerError, httpx.TimeoutException) as e:  # busy or too slow -> next model
                    log.warning("%s busy/slow after %.1fs (%s), trying next model",
                                model, time.monotonic() - start, type(e).__name__)
                    break
        raise HTTPException(503, BUSY)

    def embed(self, texts: list[str]) -> list[list[float]]:
        for attempt in range(2):
            try:
                resp = self.client.models.embed_content(
                    model=self.embed_model,
                    contents=texts,
                    config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"),
                )
                return [e.values for e in resp.embeddings]
            except (errors.ServerError, httpx.TimeoutException):
                time.sleep(1)
            except errors.ClientError as e:
                if e.code == 429:
                    break
                raise
        raise HTTPException(503, BUSY)
