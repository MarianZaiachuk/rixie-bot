[Українською](README.uk.md)

# rixie-bot

Telegram bot on `aiogram 3` connected to a local LLM running in LM Studio via its OpenAI-compatible API. Keeps per-chat message history, supports switching between the default sarcastic gamer persona (`rixie`) and a plain `assistant` mode, and includes admin commands for channel posting.

## Commands

| Command | Access | Description |
|---|---|---|
| `/start` | All | Greeting and basic usage |
| `/help` | All | List commands |
| `/clear` | All | Reset conversation history for the current chat |
| `/status` | Admin | Check LM Studio connectivity and loaded model |
| `/post <Game> \| <Score>` | Admin | Generate a short review and post it to `CHANNEL_ID` |
| `/post_welcome` | Admin | Post and pin a welcome message in `CHANNEL_ID` |

## Setup

1. Clone the repository and install dependencies:

```bash
git clone https://github.com/MarianZaiachuk/rixie-bot.git
cd rixie-bot
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Create `.env` from `.env.example` and fill in your Telegram credentials.
3. Open **LM Studio**, load a model, and start the Local Server on port `1234` (Developer tab).
4. Run the bot:

```bash
python main.py
```

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `BOT_TOKEN` | Yes | — | Token from `@BotFather` |
| `ADMIN_ID` | Yes | — | Numeric Telegram user ID of the admin |
| `CHANNEL_ID` | No | — | Channel username or ID for `/post` and `/post_welcome` |
| `LLM_URL` | No | `http://127.0.0.1:1234/v1` | Local OpenAI-compatible API base URL |
| `LLM_MODEL` | No | `local-model` | Model name sent to the API |
| `LLM_API_KEY` | No | `lm-studio` | API key string passed to `AsyncOpenAI` |
| `LLM_TIMEOUT` | No | `60.0` | Request timeout in seconds |
| `LLM_TEMPERATURE` | No | `0.7` | Sampling temperature |
| `MAX_HISTORY` | No | `20` | Max messages kept in memory per chat |
| `BOT_PERSONA` | No | `rixie` | `rixie` or `assistant` |
| `SYSTEM_PROMPT` | No | — | Custom system prompt (overrides `BOT_PERSONA`) |

## Tests

```bash
pip install -r requirements-dev.txt
pytest -v
```

## License

[MIT](LICENSE)
