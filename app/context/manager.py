import logging
from typing import List, Dict, Any

logger = logging.getLogger("aura_ai.context")

# Max token limit safety threshold for context window
MAX_CONTEXT_TOKENS = 4096


class ContextManager:

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Approximates token count (4 chars ~ 1 token average)."""
        if not text:
            return 0
        return max(1, len(text) // 4)

    @staticmethod
    def estimate_messages_tokens(messages: List[Dict[str, str]]) -> int:
        total = 0
        for m in messages:
            total += ContextManager.estimate_tokens(m.get("content", ""))
        return total

    @staticmethod
    def trim_context_history(
        messages: List[Dict[str, str]],
        max_tokens: int = MAX_CONTEXT_TOKENS
    ) -> List[Dict[str, str]]:
        """
        Trims conversation history to fit within context token limits.
        Preserves system prompts and recent conversation messages.
        """
        if not messages:
            return []

        system_messages = [m for m in messages if m.get("role") == "system"]
        conversation_messages = [m for m in messages if m.get("role") != "system"]

        system_tokens = ContextManager.estimate_messages_tokens(system_messages)
        available_tokens = max(500, max_tokens - system_tokens)

        retained = []
        accumulated_tokens = 0

        # Iterate backwards from most recent message
        for msg in reversed(conversation_messages):
            msg_tokens = ContextManager.estimate_tokens(msg.get("content", ""))
            if accumulated_tokens + msg_tokens > available_tokens:
                break
            retained.insert(0, msg)
            accumulated_tokens += msg_tokens

        return system_messages + retained
