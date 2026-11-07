import json
import time

from fastapi import HTTPException
from google import genai
from google.genai import errors, types

from app.providers.base import AIProvider


class GeminiProvider(AIProvider):
    def __init__(
        self, api_key: str, chat_model: str, embed_model: str, fallback_models: str = "", thinking_level: str = "low"
    ):
        self.client = genai.Client(api_key=api_key)
        backups = [m.strip() for m in fallback_models.split(",") if m.strip()]
        self.chat_models = [chat_model, *backups]
        self.embed_model = embed_model
        self.thinking_level = thinking_level.strip().upper()

    def _config(self, model: str) -> types.GenerateContentConfig:
        thinking = None
        if self.thinking_level and model not in self.no_thinking_cfg:
            thinking = types.ThinkingConfig(thinking_level=self.thinking_level)
        return types.GenerateContentConfig(
            response_mime_type="application/json", thinking_config=thinking
        )

    no_thinking_cfg: set = set()  # models that rejected thinking_level (older models)

    def generate_json(self, prompt: str) -> dict:
        for model in self.chat_models:
            for attempt in range(3):
                try:
                    resp = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=self._config(model),
                    )
                    return json.loads(resp.text)
                except json.JSONDecodeError:  # rare cut-off answer -> ask again
                    continue
                except errors.ServerError:  # 503 busy -> wait and retry
                    time.sleep(1 + attempt)
                except errors.ClientError as e:
                    if e.code == 429:  # rate limit on this model -> try the next one
                        break
                    if e.code == 400 and "think" in str(e).lower() and model not in self.no_thinking_cfg:
                        self.no_thinking_cfg.add(model)  # model doesn't support thinking_level; retry without it
                        continue
                    raise
        raise HTTPException(503, "The AI is busy right now. Please try again in a minute.")

    def embed(self, texts: list[str]) -> list[list[float]]:
        for attempt in range(3):
            try:
                resp = self.client.models.embed_content(
                    model=self.embed_model,
                    contents=texts,
                    config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"),
                )
                return [e.values for e in resp.embeddings]
            except errors.ServerError:
                time.sleep(2 ** attempt)
            except errors.ClientError as e:
                if e.code == 429:
                    break
                raise
        raise HTTPException(503, "The AI is busy right now. Please try again in a minute.")
