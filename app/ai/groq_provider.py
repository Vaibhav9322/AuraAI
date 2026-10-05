import logging
import asyncio
from typing import List, Dict, AsyncGenerator, Optional
from groq import AsyncGroq, GroqError

from app.ai.base import AIProvider
from app.config.settings import settings

logger = logging.getLogger("aura_ai.groq")


class GroqProvider(AIProvider):
    DEFAULT_MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.AI_API_KEY
        self.client = AsyncGroq(api_key=self.api_key) if self.api_key else None

    def _resolve_model(self, model: Optional[str]) -> str:
        model_name = model or settings.AI_MODEL or "openai/gpt-oss-120b"
        if model_name in ["llama-3.3-70b-versatile", "llama3-70b-8192", "llama3-8b-8192"]:
            return "openai/gpt-oss-120b"
        return model_name

    async def generate(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
        if not self.client:
            return "Groq API key is not configured in `.env`. Please add `AI_API_KEY=your_key` to enable live AI responses."

        model_name = self._resolve_model(model)
        models_to_try = [model_name] + [m for m in self.DEFAULT_MODELS if m != model_name]

        last_error = None
        for m in models_to_try:
            try:
                response = await self.client.chat.completions.create(
                    model=m,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2048
                )
                return response.choices[0].message.content or ""
            except Exception as e:
                logger.warning(f"Groq model {m} failed: {e}")
                last_error = e

        logger.error(f"All Groq models failed: {last_error}")
        raise last_error

    async def stream(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> AsyncGenerator[str, None]:
        if not self.client:
            mock_text = "Groq API key is not configured in `.env`. Please add `AI_API_KEY=your_key` to `.env` to enable live Groq AI responses!"
            for token in mock_text.split(" "):
                yield token + " "
                await asyncio.sleep(0.04)
            return

        model_name = self._resolve_model(model)
        models_to_try = [model_name] + [m for m in self.DEFAULT_MODELS if m != model_name]

        for m in models_to_try:
            try:
                response_stream = await self.client.chat.completions.create(
                    model=m,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2048,
                    stream=True
                )
                has_content = False
                async for chunk in response_stream:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        has_content = True
                        yield chunk.choices[0].delta.content
                if has_content:
                    return
            except Exception as e:
                logger.warning(f"Groq streaming model {m} failed: {e}")
                continue

        yield "\n\n[Error: Unable to generate stream response with available Groq models.]"
