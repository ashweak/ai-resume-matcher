from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Swap providers by changing this one value: "gemini" | "claude"
    ai_provider: str = "gemini"

    gemini_api_key: str = ""
    gemini_chat_model: str = "gemini-flash-lite-latest"  # Lite = fastest answers
    gemini_embed_model: str = "gemini-embedding-001"
    gemini_fallback_models: str = "gemini-3.8-flash,gemini-3.5-flash"
    # How much the model "thinks" before answering: minimal | low | medium | high. Lower = faster.
    gemini_thinking_level: str = "low"
    # Give up on a slow model after this many seconds and try the next one.
    gemini_timeout_seconds: int = 20

    anthropic_api_key: str = ""
    claude_chat_model: str = "claude-haiku-5-5"

    # Max AI calls per visitor (IP) per hour; 0 = unlimited. Protects the free quota.
    ai_calls_per_hour: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
