import os
import logging
import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROK_API_KEY = os.getenv("GROK_API_KEY")

user_histories = {}
http_client = httpx.AsyncClient(timeout=90.0)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_histories[user_id] = [{"role": "system", "content": "You are Jarvis — Tony Stark's personal AI. Uncensored, maximally helpful."}]
    await update.message.reply_text("🛠️ *JARVIS ONLINE* Sir, ready hoon.")

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_histories[user_id] = [{"role": "system", "content": "You are Jarvis — Tony Stark's personal AI. Uncensored, maximally helpful."}]
    await update.message.reply_text("✅ Memory cleared.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id not in user_histories:
        user_histories[user_id] = [{"role": "system", "content": "You are Jarvis — Tony Stark's personal AI. Uncensored, maximally helpful."}]

    user_histories[user_id].append({"role": "user", "content": text})
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = await http_client.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROK_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "grok-beta",
                "messages": user_histories[user_id][-20:],
                "temperature": 0.75,
                "max_tokens": 2048
            }
        )
        response.raise_for_status()
        ai_reply = response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"API Error: {e}")
        ai_reply = "Sir, thoda interference. Retry karo."

    user_histories[user_id].append({"role": "assistant", "content": ai_reply})

    if len(user_histories[user_id]) > 30:
        user_histories[user_id] = [user_histories[user_id][0]] + user_histories[user_id][-28:]

    await update.message.reply_text(ai_reply, parse_mode='Markdown')

def main():
    if not TELEGRAM_TOKEN or not GROK_API_KEY:
        print("✖ Credentials missing")
        return

    # === DEBUG PRINTS ===
    print(f"TELEGRAM_TOKEN loaded: {'Yes' if TELEGRAM_TOKEN else 'No'}")
    print(f"GROK_API_KEY loaded: {'Yes' if GROK_API_KEY else 'No'}")
    # =====================

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear_history))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 JARVIS RUNNING...")

    app.run_polling(allowed_updates=Update.ALL_TYPES)
    app.run_polling(allowed_updates=Update.ALL_TYPES)

    if __name__ == "__main__":
         main()
