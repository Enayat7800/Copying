import os
import re
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Environment variables load karna
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
EXEMPT_BOT_ID = os.getenv("EXEMPT_BOT_ID")
if EXEMPT_BOT_ID:
    EXEMPT_BOT_ID = int(EXEMPT_BOT_ID)

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Advanced URL regex pattern: ye pattern "http", "https" aur "www" se shuru hone waale links capture karega.
URL_REGEX = re.compile(r'\b((?:https?://|www\.)\S+)\b', re.IGNORECASE)

# Global sets:
ALLOWED_SENDERS = set()       # jin users ko owner permission de chuka hai
ALLOWED_CHANNELS = set()      # channels jahan messages ko delete nahin karna hai

# Helper function: authorized check
def is_authorized(user_id: int) -> bool:
    return user_id == OWNER_ID or user_id in ALLOWED_SENDERS

# Message handler jo sabhi messages ko process karega
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return  # sirf messages ko process karte hain

    message = update.message
    user = message.from_user
    chat_id = update.effective_chat.id

    # Agar message ke text mein koi URL ho
    if message.text and URL_REGEX.search(message.text):
        # Agar chat (channel) whitelisted hai, to koi deletion nahin
        if chat_id in ALLOWED_CHANNELS:
            logger.info(f"Channel {chat_id} whitelisted, message allowed.")
            return

        # Agar message sender owner ya allowed user hai, to bhi allow
        if user and is_authorized(user.id):
            logger.info(f"Authorized user {user.id} sent a message; allowed.")
            return

        # Agar message sender hamare exempt bot se hai, to allow
        if user and user.is_bot and EXEMPT_BOT_ID and user.id == EXEMPT_BOT_ID:
            logger.info(f"Message from exempt bot {EXEMPT_BOT_ID}; allowed.")
            return

        # Agar above conditions match nahin hui, to 10 sec baad message delete karne ka prayas karte hain
        await asyncio.sleep(10)
        try:
            await message.delete()
            logger.info(f"Deleted message from {user.id} in chat {chat_id} containing link.")
        except Exception as e:
            logger.error(f"Error deleting message from {user.id} in chat {chat_id}: {e}")

# Command: /allow - owner hi de sakta hai dusre user ko posting permission
async def allow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Sirf owner hi permission de sakta hai.")
        return

    if context.args:
        try:
            for uid in context.args:
                ALLOWED_SENDERS.add(int(uid))
            await update.message.reply_text("Permissions updated.")
            logger.info(f"Allowed senders updated: {ALLOWED_SENDERS}")
        except ValueError:
            await update.message.reply_text("Kripya valid user IDs dein.")
    else:
        await update.message.reply_text("Kripya user ID(s) provide karein.")

# Command: /disallow - owner hi remove kar sakta hai posting permission
async def disallow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Sirf owner hi permission remove kar sakta hai.")
        return

    if context.args:
        try:
            for uid in context.args:
                ALLOWED_SENDERS.discard(int(uid))
            await update.message.reply_text("Permissions updated.")
            logger.info(f"Allowed senders updated: {ALLOWED_SENDERS}")
        except ValueError:
            await update.message.reply_text("Kripya valid user IDs dein.")
    else:
        await update.message.reply_text("Kripya user ID(s) provide karein.")

# Command: /addchannel - kisi bhi channel ko whitelist karne ke liye.
async def addchannel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    # Agar command channel se aayi hai, to us channel ko add karo.
    if chat.type in ["channel", "supergroup", "group"]:
        ALLOWED_CHANNELS.add(chat.id)
        try:
            await update.message.reply_text(f"Ye channel ({chat.id}) whitelist mein add ho gaya.")
        except Exception as e:
            logger.error(f"Error replying in channel {chat.id}: {e}")
        logger.info(f"Channel {chat.id} added to allowed channels.")
    else:
        # Agar private chat se command aayi, to channel id argument ke roop mein de sakte hain
        if context.args:
            try:
                channel_id = int(context.args[0])
                ALLOWED_CHANNELS.add(channel_id)
                await update.message.reply_text(f"Channel {channel_id} whitelist mein add ho gaya.")
                logger.info(f"Channel {channel_id} added to allowed channels by owner.")
            except ValueError:
                await update.message.reply_text("Kripya valid channel ID dein.")
        else:
            await update.message.reply_text("Kripya channel ID provide karein ya channel se command run karein.")

# Main function: Application build karna aur handlers add karna
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Message handler: text messages (commands excluded) ke liye
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))
    # Commands
    application.add_handler(CommandHandler("allow", allow_command))
    application.add_handler(CommandHandler("disallow", disallow_command))
    application.add_handler(CommandHandler("addchannel", addchannel_command))

    # Error handler (global level)
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.error(msg="Exception while handling an update:", exc_info=context.error)
    application.add_error_handler(error_handler)

    # Bot ko polling se run karte hain
    application.run_polling()

if __name__ == '__main__':
    main()
