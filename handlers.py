"""Telegram command and message handlers."""

from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.enums import ChatAction, ParseMode
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message

from config import Settings
from llm_service import ConversationMemory, LocalLLMClient
from prompts import REVIEW_SYSTEM_PROMPT, REVIEW_TEMPLATE


def parse_review_args(raw_args: str) -> tuple[str, str] | None:
    """Parse '<Game Name> | <Score>' arguments for /post. Returns None if game is empty."""
    cleaned = raw_args.strip()
    if not cleaned:
        return None

    parts = cleaned.split("|", maxsplit=1)
    game_name = parts[0].strip()
    if not game_name:
        return None

    score = parts[1].strip() if len(parts) > 1 and parts[1].strip() else "0"
    return game_name, score


def format_review_post(game_name: str, review_text: str, score: str) -> str:
    """Format an HTML channel post with safe HTML escaping."""
    safe_game = html.escape(game_name.upper())
    safe_review = html.escape(review_text.strip())
    safe_score = html.escape(score.strip())
    return (
        f"🎮 <b>{safe_game}</b>\n\n"
        f"{safe_review}\n\n"
        f"🔥 <b>verdict: {safe_score}/10</b>\n"
        "#review #rixie"
    )


def _is_admin(message: Message, admin_id: int) -> bool:
    return message.from_user is not None and message.from_user.id == admin_id


def create_router(
    settings: Settings,
    llm: LocalLLMClient,
    memory: ConversationMemory,
) -> Router:
    """Create and configure the aiogram Router with all bot handlers."""
    router = Router()

    @router.message(CommandStart())
    async def cmd_start(message: Message) -> None:
        await message.answer(
            "Hey! I'm connected to a local LLM.\n"
            "Send any message to chat, use /clear to reset context, or /help for commands."
        )

    @router.message(Command("help"))
    async def cmd_help(message: Message) -> None:
        text = (
            "<b>Available Commands</b>\n"
            "/start — greet the bot\n"
            "/clear — clear conversation history for this chat\n"
            "/help — show this help message\n"
            "/status — check LM Studio connection (admin)\n"
            "/post &lt;Game&gt; | &lt;Score&gt; — publish a review to channel (admin)\n"
            "/post_welcome — post &amp; pin a channel welcome message (admin)"
        )
        await message.answer(text, parse_mode=ParseMode.HTML)

    @router.message(Command("clear"))
    async def cmd_clear(message: Message) -> None:
        cleared = memory.clear(message.chat.id)
        if cleared:
            await message.answer("🧹 Conversation history cleared.")
        else:
            await message.answer("Conversation history is already empty.")

    @router.message(Command("status"))
    async def cmd_status(message: Message) -> None:
        if not _is_admin(message, settings.admin_id):
            await message.answer("⛔ Admin only command.")
            return

        ok, details = await llm.check_health()
        icon = "🟢" if ok else "🔴"
        await message.answer(
            f"{icon} <b>LM Studio Status:</b> {html.escape(details)}\n"
            f"<b>Endpoint:</b> <code>{html.escape(settings.llm_url)}</code>\n"
            f"<b>Model:</b> <code>{html.escape(settings.llm_model)}</code>\n"
            f"<b>Persona:</b> <code>{html.escape(settings.bot_persona)}</code>",
            parse_mode=ParseMode.HTML,
        )

    @router.message(Command("post_welcome"))
    async def cmd_welcome(message: Message) -> None:
        if not _is_admin(message, settings.admin_id):
            await message.answer("nice try, kiddo. access denied.")
            return

        if not settings.channel_id:
            await message.answer("⚠️ CHANNEL_ID is not configured in .env.")
            return

        text = (
            "<b>shhh. keep it quiet.</b> 🤫\n\n"
            "u found the best corner of telegram. congrats.\n"
            "turn on notifications or skill issue."
        )
        try:
            sent_msg = await message.bot.send_message(
                chat_id=settings.channel_id,
                text=text,
                parse_mode=ParseMode.HTML,
            )
            await message.bot.pin_chat_message(
                chat_id=settings.channel_id,
                message_id=sent_msg.message_id,
            )
            await message.answer("✅ Welcome post sent and pinned.")
        except Exception as exc:
            await message.answer(f"⚠️ Failed to post welcome message: {exc}")

    @router.message(Command("post"))
    async def cmd_post_review(message: Message, command: CommandObject) -> None:
        if not _is_admin(message, settings.admin_id):
            return

        if not settings.channel_id:
            await message.answer("⚠️ CHANNEL_ID is not configured in .env.")
            return

        parsed = parse_review_args(command.args or "")
        if parsed is None:
            await message.answer(
                "Format: <code>/post Game Name | Score</code>",
                parse_mode=ParseMode.HTML,
            )
            return

        game_name, score = parsed
        status_msg = await message.answer(
            f"✍️ Generating review for <b>{html.escape(game_name)}</b>...",
            parse_mode=ParseMode.HTML,
        )

        prompt = REVIEW_TEMPLATE.format(game=game_name, rating=score)
        review_text, ok = await llm.request_reply(prompt, system_prompt=REVIEW_SYSTEM_PROMPT)
        if not ok:
            await status_msg.edit_text(review_text)
            return

        final_post = format_review_post(game_name, review_text, score)
        try:
            await message.bot.send_message(
                chat_id=settings.channel_id,
                text=final_post,
                parse_mode=ParseMode.HTML,
            )
            await status_msg.edit_text("✅ Posted to channel!")
        except Exception as exc:
            await status_msg.edit_text(f"❌ Failed to post: {exc}")

    @router.message(F.text)
    async def handle_text(message: Message) -> None:
        user_text = (message.text or "").strip()
        if not user_text:
            return

        await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
        history = memory.get_history(message.chat.id)
        reply, ok = await llm.request_reply(user_text=user_text, history=history)
        if ok:
            memory.append_exchange(message.chat.id, user_text, reply)
        await message.answer(reply)

    return router
