import telegram
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import logging
import time

# Replace with your bot token
BOT_TOKEN = "YOUR_BOT_TOKEN"
# Replace with your channel id where you want to copy the messages
DESTINATION_CHANNEL_ID = "YOUR_DESTINATION_CHANNEL_ID"

# Store the channels to copy messages from
SOURCE_CHANNELS = []

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)
logger = logging.getLogger(__name__)


def start(update, context):
    update.message.reply_text('Hi! I am your channel copier bot. Use /add_channel <channel_id> to add a source channel.')


def add_channel(update, context):
    try:
        channel_id = context.args[0]
        SOURCE_CHANNELS.append(channel_id)
        update.message.reply_text(f'Channel {channel_id} added to the list of channels to copy from.')
        logger.info(f"Added channel: {channel_id}")
    except (IndexError, ValueError):
        update.message.reply_text('Please provide a valid channel ID after the /add_channel command.')

def copy_message(update, context):
    message = update.effective_message

    if str(message.chat_id) in SOURCE_CHANNELS:
        try:
            context.bot.copy_message(
                chat_id = DESTINATION_CHANNEL_ID,
                from_chat_id = message.chat_id,
                message_id = message.message_id
            )
            logger.info(f"Copied message from {message.chat_id} to {DESTINATION_CHANNEL_ID}")
        except Exception as e:
            logger.error(f"Error copying message: {e}")

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_channel", add_channel))
    application.add_handler(MessageHandler(filters.ChatType.GROUPS , copy_message))
    application.add_error_handler(error)
    
    application.run_polling()
    logger.info("Bot started and is polling for updates...")

if __name__ == '__main__':
    main()
