from app.config import Settings
from app.providers.base import AIProvider


def get_provider(settings: Settings) -> AIProvider:
    if settings.ai_provider == "gemini":
        from app.providers.gemini import GeminiProvider

        return GeminiProvider(
            settings.gemini_api_key, settings.gemini_chat_model, settings.gemini_embed_model, settings.gemini_fallback_models
        )

    if settings.ai_provider == "claude":
        from app.providers.claude import ClaudeProvider
        from app.providers.gemini import GeminiProvider

        embedder = GeminiProvider(
            settings.gemini_api_key, settings.gemini_chat_model, settings.gemini_embed_model, settings.gemini_fallback_models
        )
        return ClaudeProvider(settings.anthropic_api_key, settings.claude_chat_model, embedder)

    raise ValueError(f"Unknown AI_PROVIDER: {settings.ai_provider}")
