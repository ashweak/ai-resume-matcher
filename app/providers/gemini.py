import json

from google import genai
from google.genai import types

from app.providers.base import AIProvider


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, chat_model: str, embed_model: str):
        self.client = genai.Client(api_key=api_key)
        self.chat_model = chat_model
        self.embed_model = embed_model

    def generate_json(self, prompt: str) -> dict:
        resp = self.client.models.generate_content(
            model=self.chat_model,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        return json.loads(resp.text)

    def embed(self, texts: list[str]) -> list[list[float]]:
        resp = self.client.models.embed_content(
            model=self.embed_model,
            contents=texts,
            config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"),
        )
        return [e.values for e in resp.embeddings]
