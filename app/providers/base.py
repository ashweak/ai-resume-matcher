from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Every AI provider implements this. The rest of the app only talks to this interface."""

    @abstractmethod
    def generate_json(self, prompt: str) -> dict:
        """Send a prompt and return the model's reply parsed as JSON."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""
