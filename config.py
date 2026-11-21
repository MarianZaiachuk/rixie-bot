"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class Settings:
    """Validated runtime settings for the Telegram Local LLM bot."""

    bot_token: str
    admin_id: int
    channel_id: str | None = None
    llm_url: str = "http://127.0.0.1:1234/v1"
    llm_api_key: str = "lm-studio"
    llm_model: str = "local-model"
    llm_timeout: float = 60.0
    llm_temperature: float = 0.7
    max_history: int = 20
    bot_persona: str = "rixie"
    system_prompt: str | None = None

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> Settings:
        """Build and validate Settings from an environment mapping (defaults to os.environ)."""
        env = os.environ if environ is None else environ

        bot_token = env.get("BOT_TOKEN", "").strip()
        if not bot_token:
            raise ValueError("Missing required BOT_TOKEN in environment or .env file.")

        admin_raw = env.get("ADMIN_ID", "").strip()
        if not admin_raw:
            raise ValueError("Missing required ADMIN_ID in environment or .env file.")
        try:
            admin_id = int(admin_raw)
        except ValueError as exc:
            raise ValueError(f"ADMIN_ID must be an integer, got: {admin_raw!r}") from exc

        channel_id = env.get("CHANNEL_ID", "").strip() or None
        llm_url = env.get("LLM_URL", "http://127.0.0.1:1234/v1").strip() or "http://127.0.0.1:1234/v1"
        llm_api_key = env.get("LLM_API_KEY", "lm-studio").strip() or "lm-studio"
        llm_model = env.get("LLM_MODEL", "local-model").strip() or "local-model"

        timeout_raw = env.get("LLM_TIMEOUT", "60.0").strip() or "60.0"
        try:
            llm_timeout = float(timeout_raw)
        except ValueError as exc:
            raise ValueError(f"LLM_TIMEOUT must be a number, got: {timeout_raw!r}") from exc
        if llm_timeout <= 0:
            raise ValueError(f"LLM_TIMEOUT must be positive, got: {llm_timeout}")

        temp_raw = env.get("LLM_TEMPERATURE", "0.7").strip() or "0.7"
        try:
            llm_temperature = float(temp_raw)
        except ValueError as exc:
            raise ValueError(f"LLM_TEMPERATURE must be a number, got: {temp_raw!r}") from exc

        history_raw = env.get("MAX_HISTORY", "20").strip() or "20"
        try:
            max_history = int(history_raw)
        except ValueError as exc:
            raise ValueError(f"MAX_HISTORY must be an integer, got: {history_raw!r}") from exc
        if max_history < 0:
            max_history = 0

        bot_persona = (env.get("BOT_PERSONA", "rixie").strip().lower()) or "rixie"
        system_prompt = env.get("SYSTEM_PROMPT", "").strip() or None

        return cls(
            bot_token=bot_token,
            admin_id=admin_id,
            channel_id=channel_id,
            llm_url=llm_url,
            llm_api_key=llm_api_key,
            llm_model=llm_model,
            llm_timeout=llm_timeout,
            llm_temperature=llm_temperature,
            max_history=max_history,
            bot_persona=bot_persona,
            system_prompt=system_prompt,
        )
