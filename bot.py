import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Get your bot token from Render environment variable
TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reply when user sends /start"""
    await update.message.reply_text("Hello! Your bot is running on Render.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reply when user sends /help"""
    await update.message.reply_text("Available commands: /start, /help")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    app.run_polling()

if __name__ == "__main__":
    main()
