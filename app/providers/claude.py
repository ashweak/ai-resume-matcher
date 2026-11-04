"""Optional paid provider. Not used by default (Gemini free tier is the default).
To enable: pip install anthropic, set AI_PROVIDER=claude and ANTHROPIC_API_KEY in .env."""
import json

from app.providers.base import AIProvider


class ClaudeProvider(AIProvider):
    def __init__(self, api_key: str, chat_model: str, fallback_embedder: AIProvider | None = None):
        import anthropic  # imported lazily so the package is optional

        self.client = anthropic.Anthropic(api_key=api_key)
        self.chat_model = chat_model
        # Claude has no embeddings endpoint, so embeddings come from another provider.
        self.fallback_embedder = fallback_embedder

    def generate_json(self, prompt: str) -> dict:
        msg = self.client.messages.create(
            model=self.chat_model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt + "\nReply with JSON only."}],
        )
        return json.loads(msg.content[0].text)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.fallback_embedder:
            raise RuntimeError("ClaudeProvider needs a fallback embedder (e.g. Gemini).")
        return self.fallback_embedder.embed(texts)
