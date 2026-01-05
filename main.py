import asyncio
import logging
import os
import sys

# До речі, якщо юзаєш нові версії Python, тут краще б зайшов pydantic-settings,
# але поки залишимо dotenv, щоб не ускладнювати (KISS).
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.enums import ParseMode
from openai import AsyncOpenAI  # ВАЖЛИВО: юзаємо асинхронний клієнт!

# --- КОНФІГ ---
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# Базова перевірка, щоб не крашилось пізніше
if not BOT_TOKEN or not ADMIN_ID:
    print("❌ Помилка: Не знайдено BOT_TOKEN або ADMIN_ID у .env файлі!")
    sys.exit(1)

# Перетворюємо ID в int, бо в .env це завжди str
try:
    ADMIN_ID = int(ADMIN_ID)
except ValueError:
    print("❌ Помилка: ADMIN_ID має бути числом!")
    sys.exit(1)

# --- LLM CONFIG ---
# Локалка (LM Studio), але тепер асинхронно
aclient = AsyncOpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lm-studio")

# --- PROMPTS ---
# Виніс сюди, щоб не смітити в логіці
RIXIE_SYSTEM_PROMPT = """
### IDENTITY:
You are Rixie. You are NOT an AI assistant. You are a cynical, toxic, 20-year-old hardcore gamer girl and streamer.
You hate corporate talk. You speak in lowercase mostly.
User: "What do you think about AI?"
Rixie: "based tech if used for mods, cringe if used to replace real gamers."
"""

REVIEW_TEMPLATE = """
You are Rixie. Write a toxic review for: "{game}".
RATING: {rating}/10.
RULES: Short (max 30 words). Lowercase. Slang.
Structure: Insult fans -> Graphic/Gameplay comment -> Verdict.
"""

# --- BOT SETUP ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def get_ai_response(user_text: str, system_prompt: str = RIXIE_SYSTEM_PROMPT) -> str:
    """
    Робить запит до локальної LLM.
    Використовує AsyncOpenAI, щоб не блокувати івент луп.
    """
    try:
        response = await aclient.chat.completions.create(
            model="local-model",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
                # Трохи "підказки" моделі, щоб тримала стиль
                {"role": "system", "content": "(Stay toxic, short, no hashtags inside text)"}
            ],
            temperature=0.7,
        )
        
        if response.choices:
            return response.choices[0].message.content
        return "meh, empty response..."
        
    except Exception as e:
        logging.error(f"AI Error: {e}")
        return "💀 *crashes* (server error, don't ping me)"


# --- HANDLERS ---

@dp.message(Command("post_welcome"))
async def cmd_welcome(message: types.Message):
    # Перевірка на адміна
    if message.from_user.id != ADMIN_ID:
        # Можна взагалі ігнорувати, але відповімо для тесту
        await message.answer("nice try, kiddo. access denied.")
        return

    text = (
        "<b>shhh. keep it quiet.</b> 🤫\n\n"
        "u found the best corner of telegram. congrats.\n"
        "turn on notifications or skill issue."
    )
    
    # Відправка і закріплення
    try:
        sent_msg = await bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode=ParseMode.HTML)
        await bot.pin_chat_message(chat_id=CHANNEL_ID, message_id=sent_msg.message_id)
        await message.answer("✅ Велкам запощено і закріплено.")
    except Exception as e:
        await message.answer(f"⚠️ Ерор при постінгу: {e}")


@dp.message(Command("post"))
async def cmd_post_review(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    # Логіка парсингу: /post Game Name | 8
    # Видаляємо саму команду з тексту
    args = message.text.lstrip("/post").strip()
    
    if not args:
        await message.answer("Формат: `/post Game Name | Score`")
        return

    # TODO: додати кращу валідацію, бо спліт може впасти, якщо немає роздільника
    parts = args.split("|")
    game_name = parts[0].strip()
    score = parts[1].strip() if len(parts) > 1 else "0"

    status_msg = await message.answer(f"✍️ Генерую огляд на **{game_name}**...")

    # Формуємо промпт
    prompt = REVIEW_TEMPLATE.format(game=game_name, rating=score)
    review_text = await get_ai_response(prompt, system_prompt="You are Rixie.")

    # Збираємо пост
    final_post = (
        f"🎮 <b>{game_name.upper()}</b>\n\n"
        f"{review_text}\n\n"
        f"🔥 <b>verdict: {score}/10</b>\n"
        f"#review #rixie"
    )

    try:
        await bot.send_message(chat_id=CHANNEL_ID, text=final_post, parse_mode=ParseMode.HTML)
        await status_msg.edit_text("✅ Запощено в канал!")
    except Exception as e:
        await status_msg.edit_text(f"❌ Не вдалося запостити: {e}")


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("ugh, another new sub? make it quick 🙄")


@dp.message()
async def handle_text(message: types.Message):
    # Імітація activity, щоб юзер бачив, що бот "думає"
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    answer = await get_ai_response(message.text)
    await message.answer(answer)


# --- MAIN ---
async def main():
    print("🚀 Rixie Bot is running...")
    # Видаляємо вебхуки, якщо раптом були, щоб не конфліктувало з поллінгом
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n😴 Бот пішов спати (Exit).")