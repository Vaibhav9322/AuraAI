import logging
import asyncio
from typing import List, Dict, AsyncGenerator, Optional
from anthropic import AsyncAnthropic

from app.ai.base import AIProvider
from app.config.settings import settings

logger = logging.getLogger("aura_ai.anthropic")


class AnthropicProvider(AIProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.AI_API_KEY
        self.client = AsyncAnthropic(api_key=self.api_key) if self.api_key else None

    async def generate(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
        if not self.client:
            return "Anthropic API key is not configured. Please set `AI_API_KEY` in `.env`."

        model_name = model or settings.AI_MODEL or "claude-3-5-sonnet-20241022"
        system_prompt = ""
        filtered_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                filtered_messages.append({"role": msg["role"], "content": msg["content"]})

        try:
            kwargs = {
                "model": model_name,
                "messages": filtered_messages,
                "max_tokens": 2048,
                "temperature": 0.7
            }
            if system_prompt:
                kwargs["system"] = system_prompt

            response = await self.client.messages.create(**kwargs)
            return response.content[0].text if response.content else ""
        except Exception as e:
            logger.error(f"Anthropic generation error: {e}")
            raise e

    async def stream(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> AsyncGenerator[str, None]:
        if not self.client:
            mock_text = "Anthropic API key is not configured in `.env`. Please add `AI_API_KEY=your_key` to enable live Claude responses!"
            for token in mock_text.split(" "):
                yield token + " "
                await asyncio.sleep(0.04)
            return

        model_name = model or settings.AI_MODEL or "claude-3-5-sonnet-20241022"
        system_prompt = ""
        filtered_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                filtered_messages.append({"role": msg["role"], "content": msg["content"]})

        try:
            kwargs = {
                "model": model_name,
                "messages": filtered_messages,
                "max_tokens": 2048,
                "temperature": 0.7
            }
            if system_prompt:
                kwargs["system"] = system_prompt

            async with self.client.messages.stream(**kwargs) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            yield f"\n\n[Error: {str(e)}]"
