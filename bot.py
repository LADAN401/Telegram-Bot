#!/usr/bin/env python3
"""
telegram_ai_bot.py
Simple Telegram bot that uses OpenAI (optional).
Set environment variables:
  TELEGRAM_TOKEN  -> your bot token (required)
  OPENAI_API_KEY  -> your OpenAI API key (optional)
If OPENAI_API_KEY is missing, the bot falls back to a simple Hausa/English responder.
"""

import os
import asyncio
import json
import logging
from typing import Optional

import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# --- Configuration ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")  # required
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")     # optional

if not TELEGRAM_TOKEN:
    raise SystemExit("Error: TELEGRAM_TOKEN environment variable is required.")

# OpenAI helper (simple, uses Chat Completions API)
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = "gpt-3.5-turbo"  # safe default; change if you want a different model

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- OpenAI call function ---
def ask_openai_chat(user_message: str, system_prompt: Optional[str] = None) -> Optional[str]:
    """
    Send a chat request to OpenAI. Returns the assistant reply text or None on failure.
    Uses requests (no external OpenAI library dependency).
    """
    if not OPENAI_API_KEY:
        return None

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": OPENAI_MODEL,
        "messages": messages,
        "max_tokens": 512,
        "temperature": 0.7,
        "n": 1,
    }

    try:
        resp = requests.post(OPENAI_API_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # Navigate response safely
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.exception("OpenAI request failed: %s", e)
        return None

# --- Bot command handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Assalamu alaikum! 👋\n"
        "Ni bot ne — zan iya tattaunawa da kai.\n\n"
        "Commands:\n"
        "/help - taimako\n\n"
        "Just send me any message and I'll reply. (If you set OPENAI_API_KEY the bot replies using OpenAI.)"
    )
    await update.message.reply_text(text)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Help:\n"
        "• Send any text and I'll reply.\n"
        "• I can speak Hausa and English.\n"
        "Note: for smarter replies set the OPENAI_API_KEY environment variable."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text or ""
    user_first_name = update.effective_user.first_name or "User"

    # If OpenAI key present -> query OpenAI
    if OPENAI_API_KEY:
        # small system prompt to prefer Hausa but fall back to English if user uses English
        system_prompt = (
            "You are a helpful assistant. Prefer replying in Hausa if the user's message appears to be in Hausa; "
            "otherwise reply in the user's language. Keep replies concise and friendly."
        )
        await update.message.chat.send_action("typing")
        reply = await asyncio.get_event_loop().run_in_executor(
            None, ask_openai_chat, user_text, system_prompt
        )
        if reply:
            # Ensure message isn't too long for Telegram
            if len(reply) > 4096:
                reply = reply[:4000] + "\n\n[truncated]"
            await update.message.reply_text(reply)
            return
        else:
            # fallback below if OpenAI fails
            logger.warning("OpenAI returned no reply; falling back to local responder.")

    # Fallback simple responder (Hausa + echo)
    # Try detect simple Hausa keywords for a friendlier reply
    hausa_keywords = ["ina", "yaya", "lafiya", "na gode", "sannu", "assalamu", "salam", "kwanaki", "me"]
    user_lower = user_text.lower()
    if any(k in user_lower for k in hausa_keywords):
        fallback = f"Na ji sakonka, {user_first_name}. 🌸\nKa/ki rubuta: \"{user_text}\". Zan iya taimaka maka/ki — menene kake/kike so na yi?"
    else:
        fallback = f"I heard you: \"{user_text}\".\nYou can ask me questions or say hi (e.g., 'Assalamu')."

    await update.message.reply_text(fallback)

# optional: simple /echo command
async def echo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /echo your message")
    else:
        await update.message.reply_text(" ".join(args))

# --- Main entrypoint ---
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("echo", echo_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot starting... (press Ctrl-C to stop)")
    app.run_polling()

if __name__ == "__main__":
    main()
