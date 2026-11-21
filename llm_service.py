"""Local OpenAI-compatible LLM client and per-chat conversation memory."""

from __future__ import annotations

import logging
from collections import deque

import openai
from openai import AsyncOpenAI

from config import Settings
from prompts import resolve_system_prompt

logger = logging.getLogger(__name__)


class ConversationMemory:
    """In-memory bounded conversation history keyed by Telegram chat ID."""

    def __init__(self, max_messages: int = 20) -> None:
        self.max_messages = max(0, max_messages)
        self._store: dict[int, deque[dict[str, str]]] = {}

    def get_history(self, chat_id: int) -> list[dict[str, str]]:
        """Return a shallow copy of stored messages for chat_id."""
        if self.max_messages == 0:
            return []
        history = self._store.get(chat_id)
        return list(history) if history else []

    def append_exchange(self, chat_id: int, user_text: str, assistant_text: str) -> None:
        """Append one user/assistant exchange, trimming oldest messages beyond max_messages."""
        if self.max_messages == 0:
            return
        if chat_id not in self._store:
            self._store[chat_id] = deque(maxlen=self.max_messages)
        self._store[chat_id].append({"role": "user", "content": user_text})
        self._store[chat_id].append({"role": "assistant", "content": assistant_text})

    def clear(self, chat_id: int) -> bool:
        """Clear stored history for chat_id. Returns True if any messages were cleared."""
        existed = chat_id in self._store and len(self._store[chat_id]) > 0
        self._store.pop(chat_id, None)
        return existed


class LocalLLMClient:
    """Async client wrapper for LM Studio / OpenAI-compatible local inference servers."""

    def __init__(self, settings: Settings, client: AsyncOpenAI | None = None) -> None:
        self.settings = settings
        self.default_system_prompt = resolve_system_prompt(
            settings.bot_persona, settings.system_prompt
        )
        self._client = client or AsyncOpenAI(
            base_url=settings.llm_url,
            api_key=settings.llm_api_key,
            timeout=settings.llm_timeout,
        )

    def build_messages(
        self,
        user_text: str,
        history: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
    ) -> list[dict[str, str]]:
        """Build a valid OpenAI message sequence with a single leading system prompt."""
        sys_content = (system_prompt or self.default_system_prompt).strip()
        messages: list[dict[str, str]] = [{"role": "system", "content": sys_content}]
        if history:
            for item in history:
                role = item.get("role")
                content = item.get("content")
                if role in ("user", "assistant") and content:
                    messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_text})
        return messages

    async def request_reply(
        self,
        user_text: str,
        history: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
    ) -> tuple[str, bool]:
        """Request a chat completion and return (reply_text, succeeded)."""
        messages = self.build_messages(
            user_text=user_text,
            history=history,
            system_prompt=system_prompt,
        )
        try:
            response = await self._client.chat.completions.create(
                model=self.settings.llm_model,
                messages=messages,
                temperature=self.settings.llm_temperature,
            )
            if not response.choices:
                return "⚠️ Local LLM returned an empty choice list.", False

            content = response.choices[0].message.content
            if not content or not content.strip():
                return "⚠️ Local LLM returned an empty response.", False

            return content.strip(), True

        except openai.APITimeoutError as exc:
            logger.error("LM Studio timeout (%ss): %s", self.settings.llm_timeout, exc)
            return (
                "⏳ Local LLM timed out (the model may still be loading into memory). "
                "Please try again in a moment."
            ), False
        except openai.APIConnectionError as exc:
            logger.error("LM Studio connection error (%s): %s", self.settings.llm_url, exc)
            return (
                "🔌 Local LLM server is unreachable. "
                "Make sure LM Studio Local Server is running."
            ), False
        except openai.APIStatusError as exc:
            logger.error("LM Studio API status error (%s): %s", exc.status_code, exc)
            return f"⚠️ Local LLM returned HTTP {exc.status_code}.", False
        except Exception as exc:
            logger.exception("Unexpected LLM error: %s", exc)
            return "💀 Local LLM error occurred. Check the bot logs for details.", False

    async def generate_reply(
        self,
        user_text: str,
        history: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
    ) -> str:
        """Convenience wrapper returning only the reply text."""
        reply, _ = await self.request_reply(
            user_text=user_text,
            history=history,
            system_prompt=system_prompt,
        )
        return reply

    async def check_health(self) -> tuple[bool, str]:
        """Check whether the local LLM endpoint is reachable and list loaded models."""
        try:
            models = await self._client.models.list()
            ids = [m.id for m in getattr(models, "data", []) if getattr(m, "id", None)]
            if ids:
                return True, f"Online ({', '.join(ids[:3])})"
            return True, "Online (no model loaded or model ID hidden)"
        except openai.APITimeoutError:
            return False, f"Timeout waiting for {self.settings.llm_url}"
        except openai.APIConnectionError:
            return False, f"Offline (cannot connect to {self.settings.llm_url})"
        except Exception as exc:
            return False, f"Error: {exc}"

    async def close(self) -> None:
        """Close the underlying async HTTP client."""
        await self._client.close()
