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
user_cooldowns = {}
ADULT_KEYWORDS = ["porn", "adult", "xxx", "nsfw", "18+", "explicit", "sex", "hot"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📁 **File/Video to Link Bot**\n\nकिसी भी फ़ाइल या वीडियो को भेजें, मैं डाउनलोड लिंक दूंगा!")

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id
    current_time = time.time()

    # Cooldown check
    if user_id in user_cooldowns and (current_time - user_cooldowns[user_id] < 60):
        await update.message.reply_text("⏳ 1 मिनट के बाद नई फ़ाइल भेजें।")
        return

    # Get file details
    if update.message.document:
        file = update.message.document
    elif update.message.video:
        file = update.message.video
    else:
        return

    file_name = file.file_name or "file"
    file_size = file.file_size / (1024 * 1024)  # MB में

    # Adult content check
    if any(keyword in file_name.lower() for keyword in ADULT_KEYWORDS):
        await update.message.reply_text("🚫 Adult content डिटेक्ट हुआ। आपको ब्लॉक किया गया है!")
        return

    # File size check (2GB = 2000MB)
    if file_size > 2000:
        await update.message.reply_text("❌ फ़ाइल 2GB से बड़ी है!")
        return

    # Generate Telegram direct link
    try:
        tg_file = await context.bot.get_file(file.file_id)
        download_url = f"https://api.telegram.org/file/bot{os.environ['TOKEN']}/{tg_file.file_path}"
        
        # Send instructions with link
        await update.message.reply_text(
            f"✅ **{file_name} का डाउनलोड लिंक:**\n\n"
            f"{download_url}\n\n"
            "⚠️ **नोट:**\n"
            "1. लिंक 1 घंटे तक वैध है।\n"
            "2. डाउनलोड करने के लिए लिंक पर **राइट-क्लिक करें → 'Save link as...' चुनें**।\n"
            "3. वीडियो/फ़ाइलें 2GB तक सपोर्ट हैं।"
        )
        user_cooldowns[user_id] = current_time
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ लिंक जनरेट करने में त्रुटि!")

def main():
    TOKEN = os.environ.get("TOKEN")
    if not TOKEN:
        raise ValueError("TOKEN environment variable सेट नहीं है!")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.VIDEO, handle_media))
    
    logger.info("Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
