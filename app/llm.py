from abc import ABC, abstractmethod

from anthropic import Anthropic

from app.config import get_settings

settings = get_settings()


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, system: str, user: str) -> str:
        """Send a system prompt and a user prompt, return the model’s text reply."""


class AnthropicProvider(LLMProvider):
    def __init__(self) -> None:
        self.client = Anthropic(api_key=settings.anthropic_api_key)

    def generate(self, system: str, user: str) -> str:
        message = self.client.messages.create(
            model=settings.llm_model,
            max_tokens=1000,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(
            block.text for block in message.content if block.type == "text"
        )


def get_llm_provider() -> LLMProvider:
    return AnthropicProvider()