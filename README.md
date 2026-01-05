# 🎮 Rixie - Toxic AI Gamer Girl Bot

A Telegram bot powered by a **Local LLM** (via LM Studio) and `aiogram 3.x`.
The persona is "Rixie" — a cynical, toxic streamer who reviews games and hates corporate slang.

## ⚡ Features
- **Local LLM Integration:** Uses OpenAI API format to connect to local models (Mistral, Llama 3, etc.).
- **Async Architecture:** Fully asynchronous handling via `aiogram` and `AsyncOpenAI`.
- **Persona Management:** Strict system prompts to maintain the toxic gamer character.
- **Admin Tools:** Commands to post reviews directly to a channel.

## 🛠 Tech Stack
- **Python 3.10+**
- **Aiogram 3** (Telegram Bot API)
- **OpenAI Lib** (pointing to Localhost)
- **LM Studio** (for running the LLM)

## 🚀 How to Run

1. **Clone the repo**
   ```bash
   git clone [https://github.com/MarchikZ/rixie-bot.git](https://github.com/MarchikZ/rixie-bot.git)
   cd rixie-bot
   
   
2. Install dependencies
*Bash*
pip install -r requirements.txt

3. Configure Environment
  Rename .env.example to .env.
  Add your Telegram Bot Token and Admin ID.

4. Start LM Studio
  Load your preferred model (e.g., Hermes-2-Pro-Llama-3).
  Start the Local Inference Server on port 1234.

5. Run the bot
  *Bash*
python main.py

## 📝 Usage
/post Game Name | Score - Generate a toxic review and post it to the channel (Admin only).
Chat with the bot to get roasted.

## ⚠️ Disclaimer
The AI persona is designed to be rude/toxic for entertainment purposes. Don't take it personally.
