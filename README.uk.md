[English](README.md)

# rixie-bot

Telegram-бот на `aiogram 3`, підключений до локальної LLM у LM Studio через OpenAI-сумісний API. Зберігає контекст діалогу окремо для кожного чату, вміє перемикатися між персонажем `rixie` та звичайним режимом `assistant`, а також має адмін-команди для публікації постів у канал.

## Команди

| Команда | Доступ | Опис |
|---|---|---|
| `/start` | Усі | Привітання та коротка довідка |
| `/help` | Усі | Список доступних команд |
| `/clear` | Усі | Очистити історію діалогу в поточному чаті |
| `/status` | Адмін | Перевірити з'єднання з LM Studio та активну модель |
| `/post <Гра> \| <Оцінка>` | Адмін | Згенерувати короткий огляд і опублікувати в `CHANNEL_ID` |
| `/post_welcome` | Адмін | Надіслати та закріпити вітальний пост у `CHANNEL_ID` |

## Запуск

1. Клонуйте репозиторій і встановіть залежності:

```bash
git clone https://github.com/MarianZaiachuk/rixie-bot.git
cd rixie-bot
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Скопіюйте `.env.example` у `.env` і вкажіть токен бота та свій Telegram ID.
3. У **LM Studio** завантажте модель і запустіть Local Server на порту `1234`.
4. Запустіть бота:

```bash
python main.py
```

## Налаштування (`.env`)

| Змінна | Обов'язкова | За замовчуванням | Опис |
|---|---|---|---|
| `BOT_TOKEN` | Так | — | Токен бота від `@BotFather` |
| `ADMIN_ID` | Так | — | Числовий Telegram ID адміністратора |
| `CHANNEL_ID` | Ні | — | Канал для `/post` і `/post_welcome` (`@username` або ID) |
| `LLM_URL` | Ні | `http://127.0.0.1:1234/v1` | URL локального OpenAI-сумісного сервера |
| `LLM_MODEL` | Ні | `local-model` | Назва моделі для API-запитів |
| `LLM_API_KEY` | Ні | `lm-studio` | Ключ для `AsyncOpenAI` |
| `LLM_TIMEOUT` | Ні | `60.0` | Таймаут запиту в секундах |
| `LLM_TEMPERATURE` | Ні | `0.7` | Температура генерації |
| `MAX_HISTORY` | Ні | `20` | Максимум повідомлень в історії на чат |
| `BOT_PERSONA` | Ні | `rixie` | `rixie` або `assistant` |
| `SYSTEM_PROMPT` | Ні | — | Власний системний промпт (перевизначає `BOT_PERSONA`) |

## Тести

```bash
pip install -r requirements-dev.txt
pytest -v
```

## Ліцензія

[MIT](LICENSE)
