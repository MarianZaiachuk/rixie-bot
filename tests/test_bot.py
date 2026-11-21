"""Unit and async tests for rixie-bot."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import httpx
import openai
import pytest

from config import Settings
from handlers import format_review_post, parse_review_args
from llm_service import ConversationMemory, LocalLLMClient
from prompts import PERSONA_PROMPTS, resolve_system_prompt


class _FakeCompletions:
    def __init__(self, result_or_exc):
        self._result_or_exc = result_or_exc
        self.calls: list[dict] = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        if isinstance(self._result_or_exc, Exception):
            raise self._result_or_exc
        return self._result_or_exc


class _FakeOpenAIClient:
    def __init__(self, result_or_exc):
        self.completions = _FakeCompletions(result_or_exc)
        self.chat = SimpleNamespace(completions=self.completions)

    async def close(self) -> None:
        return None


def test_settings_from_env_valid_and_defaults() -> None:
    cfg = Settings.from_env({"BOT_TOKEN": "123:abc", "ADMIN_ID": "42"})
    assert cfg.bot_token == "123:abc"
    assert cfg.admin_id == 42
    assert cfg.llm_url == "http://127.0.0.1:1234/v1"
    assert cfg.bot_persona == "rixie"
    assert cfg.max_history == 20


def test_settings_from_env_custom_values() -> None:
    cfg = Settings.from_env(
        {
            "BOT_TOKEN": "999:xyz",
            "ADMIN_ID": "1001",
            "CHANNEL_ID": "@my_chan",
            "LLM_URL": "http://localhost:5555/v1",
            "BOT_PERSONA": "Assistant",
            "MAX_HISTORY": "12",
        }
    )
    assert cfg.channel_id == "@my_chan"
    assert cfg.llm_url == "http://localhost:5555/v1"
    assert cfg.bot_persona == "assistant"
    assert cfg.max_history == 12


def test_settings_from_env_validation_errors() -> None:
    with pytest.raises(ValueError, match="BOT_TOKEN"):
        Settings.from_env({"ADMIN_ID": "42"})

    with pytest.raises(ValueError, match="ADMIN_ID"):
        Settings.from_env({"BOT_TOKEN": "123:abc", "ADMIN_ID": "not_an_int"})


def test_resolve_system_prompt() -> None:
    assert resolve_system_prompt("assistant") == PERSONA_PROMPTS["assistant"]
    assert resolve_system_prompt("rixie", "custom prompt") == "custom prompt"


def test_conversation_memory_bounds_and_isolation() -> None:
    mem = ConversationMemory(max_messages=4)
    mem.append_exchange(1, "u1", "a1")
    mem.append_exchange(1, "u2", "a2")
    mem.append_exchange(1, "u3", "a3")
    mem.append_exchange(2, "other", "reply")

    h1 = mem.get_history(1)
    assert [m["content"] for m in h1] == ["u2", "a2", "u3", "a3"]
    assert len(mem.get_history(2)) == 2

    assert mem.clear(1) is True
    assert mem.clear(1) is False
    assert mem.get_history(1) == []
    assert len(mem.get_history(2)) == 2


def test_local_llm_client_message_order_and_history() -> None:
    fake_resp = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="  solid indie gem  "))]
    )
    fake_client = _FakeOpenAIClient(fake_resp)
    cfg = Settings(bot_token="t", admin_id=1, bot_persona="assistant")
    llm = LocalLLMClient(cfg, client=fake_client)

    history = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]
    reply, ok = asyncio.run(llm.request_reply("how are you?", history=history))

    assert ok is True
    assert reply == "solid indie gem"
    sent_messages = fake_client.completions.calls[0]["messages"]
    assert sent_messages[0]["role"] == "system"
    assert all(m["role"] != "system" for m in sent_messages[1:])
    assert [m["role"] for m in sent_messages] == ["system", "user", "assistant", "user"]


def test_local_llm_client_error_handling() -> None:
    cfg = Settings(bot_token="t", admin_id=1)
    req = httpx.Request("POST", "http://127.0.0.1:1234/v1/chat/completions")

    llm_conn = LocalLLMClient(cfg, client=_FakeOpenAIClient(openai.APIConnectionError(request=req)))
    reply_conn, ok_conn = asyncio.run(llm_conn.request_reply("ping"))
    assert ok_conn is False
    assert "unreachable" in reply_conn.lower()

    llm_timeout = LocalLLMClient(cfg, client=_FakeOpenAIClient(openai.APITimeoutError(request=req)))
    reply_to, ok_to = asyncio.run(llm_timeout.request_reply("ping"))
    assert ok_to is False
    assert "timed out" in reply_to.lower()

    llm_empty = LocalLLMClient(cfg, client=_FakeOpenAIClient(SimpleNamespace(choices=[])))
    reply_empty, ok_empty = asyncio.run(llm_empty.request_reply("ping"))
    assert ok_empty is False
    assert "empty" in reply_empty.lower()


def test_parse_review_args_regression() -> None:
    # Regression test: old str.lstrip('/post') broke game names starting with p/o/s/t
    assert parse_review_args("stray | 8") == ("stray", "8")
    assert parse_review_args("outer wilds | 10") == ("outer wilds", "10")
    assert parse_review_args("Portal 2") == ("Portal 2", "0")
    assert parse_review_args("   ") is None
    assert parse_review_args(" | 7") is None


def test_format_review_post_escapes_html() -> None:
    rendered = format_review_post("A < B & C", "10/10 <best> & clean", "9")
    assert "A &lt; B &amp; C" in rendered
    assert "10/10 &lt;best&gt; &amp; clean" in rendered
    assert "<b>verdict: 9/10</b>" in rendered
