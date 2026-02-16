# ==================== src/llm.py ====================
"""Abstraction layer for Large Language Model providers."""

from abc import ABC, abstractmethod
import logging
import time
from config import GIGACHAT_CREDENTIALS, LLM_PROVIDER

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Base class for LLM providers."""

    @abstractmethod
    def ask(self, prompt: str) -> str:
        """Send a prompt to the model and return the answer."""
        pass

    def summarize(self, dialog: str) -> str:
        """Generate a summary of a dialog using the model."""
        from . import prompts
        prompt = prompts.create_summary_prompt(dialog)
        return self.ask(prompt)


class GigaChatProvider(LLMProvider):
    """GigaChat implementation."""

    def __init__(self, credentials: str):
        from gigachat import GigaChat
        self.client = GigaChat(
            credentials=credentials,
            verify_ssl_certs=False,
            model="GigaChat",
            timeout=30,
        )

    def ask(self, prompt: str, retries: int = 3) -> str:
        for attempt in range(retries):
            try:
                response = self.client.chat(prompt)
                return response.choices[0].message.content
            except Exception as e:
                logger.exception(f"GigaChat error (attempt {attempt+1}/{retries}): {e}")
                if attempt == retries - 1:
                    raise
                time.sleep(1 * (attempt + 1))
        raise RuntimeError("Unreachable")  # never reached


# Provider factory
_provider = None


def get_provider() -> LLMProvider:
    """Return the configured LLM provider instance (singleton)."""
    global _provider
    if _provider is None:
        if LLM_PROVIDER == 'gigachat':
            _provider = GigaChatProvider(GIGACHAT_CREDENTIALS)
        # elif LLM_PROVIDER == 'openai':
        #     _provider = OpenAIProvider(...)
        else:
            raise ValueError(f"Unknown LLM provider: {LLM_PROVIDER}")
    return _provider


def ask(prompt: str) -> str:
    """Convenience function: ask the configured LLM."""
    return get_provider().ask(prompt)


def summarize(dialog: str) -> str:
    """Convenience function: summarize a dialog using the configured LLM."""
    return get_provider().summarize(dialog)