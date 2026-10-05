from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncGenerator, Optional


class AIProvider(ABC):
    """Abstract Base Class for AI Providers."""

    @abstractmethod
    async def generate(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
        """Non-streaming text generation."""
        pass

    @abstractmethod
    async def stream(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> AsyncGenerator[str, None]:
        """Streaming response generator emitting text chunks."""
        pass
