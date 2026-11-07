import json
import time

from fastapi import HTTPException
from google import genai
from google.genai import errors, types

from app.providers.base import AIProvider


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, chat_model: str, embed_model: str, fallback_models: str = ""):
        self.client = genai.Client(api_key=api_key)
        backups = [m.strip() for m in fallback_models.split(",") if m.strip()]
        self.chat_models = [chat_model, *backups]
        self.embed_model = embed_model

    def generate_json(self, prompt: str) -> dict:
        for model in self.chat_models:
            for attempt in range(3):
                try:
                    resp = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(response_mime_type="application/json"),
                    )
                    return json.loads(resp.text)
                except errors.ServerError:  # 503 busy -> wait and retry
                    time.sleep(2 ** attempt)
                except errors.ClientError as e:
                    if e.code == 429:  # rate limit on this model -> try the next one
                        break
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
