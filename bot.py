from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
import time
import logging

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global variables
user_cooldowns = {}  # Format: {user_id: last_request_time}
ADULT_KEYWORDS = ["porn", "adult", "xxx", "nsfw", "18+", "explicit"]  # Add more keywords as needed

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎉 **File to Direct Link Bot**\n\nकिसी भी फ़ाइल को भेजें, और मैं आपको उसका डायरेक्ट डाउनलोड लिंक दूंगा!")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id
    current_time = time.time()

    # Cooldown check (1 मिनट)
    if user_id in user_cooldowns and (current_time - user_cooldowns[user_id] < 60):
        await update.message.reply_text("⏳ 1 मिनट के बाद नई फ़ाइल भेजें।")
        return

    # Adult content check (फ़ाइल नाम से)
    document = update.message.document
    file_name = document.file_name or ""
    if any(keyword in file_name.lower() for keyword in ADULT_KEYWORDS):
        await update.message.reply_text("🚫 Adult content डिटेक्ट हुआ। आपको ब्लॉक किया गया है!")
        return

    # Generate Telegram direct link
    try:
        tg_file = await context.bot.get_file(document.file_id)
        download_url = f"https://api.telegram.org/file/bot{os.environ['TOKEN']}/{tg_file.file_path}"
        await update.message.reply_text(
            f"✅ **डाउनलोड लिंक:**\n\n{download_url}\n\n"
            "⚠️ लिंक 1 घंटे तक वैध रहेगा।\n"
            "Chrome में सीधे डाउनलोड शुरू करने के लिए लिंक पर राइट-क्लिक करें > 'Save link as...' चुनें।"
        )
        user_cooldowns[user_id] = current_time  # Update cooldown
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ लिंक जनरेट करने में त्रुटि!")

def main():
    TOKEN = os.environ.get("TOKEN")
    if not TOKEN:
        raise ValueError("Environment variable 'TOKEN' not set!")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    logger.info("Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
