"""Application entrypoint for the Local LLM Telegram Bot."""

from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from config import Settings
from handlers import create_router
from llm_service import ConversationMemory, LocalLLMClient


async def run_bot() -> None:
    """Initialize dependencies, start Telegram long polling, and clean up on exit."""
    load_dotenv()
    settings = Settings.from_env()

    llm = LocalLLMClient(settings)
    memory = ConversationMemory(max_messages=settings.max_history)
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(create_router(settings=settings, llm=llm, memory=memory))

    logging.info(
        "Starting bot (persona=%s, llm_url=%s, model=%s)",
        settings.bot_persona,
        settings.llm_url,
        settings.llm_model,
    )

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await llm.close()
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )
    try:
        asyncio.run(run_bot())
    except ValueError as exc:
        logging.error("Configuration error: %s", exc)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n😴 Bot stopped.")
