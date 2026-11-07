from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Swap providers by changing this one value: "gemini" | "claude"
    ai_provider: str = "gemini"

    gemini_api_key: str = ""
    gemini_chat_model: str = "gemini-3.8-flash"
    gemini_embed_model: str = "gemini-embedding-001"
    gemini_fallback_models: str = ""
    # How much the model "thinks" before answering: minimal | low | medium | high. Lower = faster.
    gemini_thinking_level: str = "low"

    anthropic_api_key: str = ""
    claude_chat_model: str = "claude-haiku-5-5"

    # Max AI calls per visitor (IP) per hour; 0 = unlimited. Protects the free quota.
    ai_calls_per_hour: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
