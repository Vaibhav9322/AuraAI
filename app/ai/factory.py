import logging
import os
from typing import Optional
from app.ai.base import AIProvider
from app.ai.groq_provider import GroqProvider
from app.ai.openai_provider import OpenAIProvider
from app.ai.anthropic_provider import AnthropicProvider
from app.config.settings import settings

logger = logging.getLogger("aura_ai.factory")


class AIProviderFactory:
    @staticmethod
    def get_provider(provider_name: Optional[str] = None, api_key: Optional[str] = None) -> AIProvider:
        name = (provider_name or settings.AI_PROVIDER or "gemini").lower().strip()

        if name in ["gemini", "google"]:
            base_url = os.getenv("AI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
            return OpenAIProvider(api_key=api_key, base_url=base_url)
        elif name == "openrouter":
            base_url = os.getenv("AI_BASE_URL", "https://openrouter.ai/api/v1")
            return OpenAIProvider(api_key=api_key, base_url=base_url)
        elif name in ["openai", "openai-compatible"]:
            base_url = os.getenv("AI_BASE_URL", None)
            return OpenAIProvider(api_key=api_key, base_url=base_url)
        elif name in ["anthropic", "claude"]:
            return AnthropicProvider(api_key=api_key)
        elif name == "groq":
            return GroqProvider(api_key=api_key)
        else:
            base_url = os.getenv("AI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
            return OpenAIProvider(api_key=api_key, base_url=base_url)
