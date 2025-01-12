import logging
import asyncio
import os
from telethon import TelegramClient, events, sync
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import InputPeerChannel
from telethon.tl.functions.messages import DeleteMessagesRequest

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# Get API credentials and bot token from environment variables
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")


if not API_ID:
    logger.error("API_ID not found in environment variables. Deployment will not work.")
    exit()  # Exit if API_ID is missing
else:
    logger.info("API_ID found in environment variables.")


if not API_HASH:
    logger.error("API_HASH not found in environment variables. Deployment will not work.")
    exit()  # Exit if API_HASH is missing
else:
    logger.info("API_HASH found in environment variables.")


if not BOT_TOKEN:
    logger.error("BOT_TOKEN not found in environment variables. Deployment will not work.")
    exit()  # Exit if BOT_TOKEN is missing
else:
    logger.info("BOT_TOKEN found in environment variables.")


if not CHANNEL_ID:
    logger.error("CHANNEL_ID not found in environment variables. Deployment will not work.")
    exit()
else:
  logger.info("CHANNEL_ID found in environment variables.")

try:
   CHANNEL_ID = int(CHANNEL_ID)
   logger.info(f"Channel ID found and converted to int {CHANNEL_ID}")
except ValueError:
  logger.error(f"Invalid CHANNEL_ID: {CHANNEL_ID}, Please provide an integer value. Deployment will not work.")
  exit()

# Create Telethon client
client = TelegramClient('anon', int(API_ID), API_HASH).start(bot_token=BOT_TOKEN)


@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Sends a welcome message when the /start command is issued."""
    logger.info(f"User {event.sender_id} started the bot.")
    await event.respond("Hi! I'm your personal file finder. Send me a file name and I'll search for it in the channel.")


@client.on(events.NewMessage)
async def search_file_handler(event):
    """Handles text messages and starts file search process."""
    if event.is_private and not event.message.text.startswith('/'):
       user_input = event.message.text
       logger.info(f"User {event.sender_id} search: {user_input}")
       found_files = await search_file(user_input, CHANNEL_ID)
       if found_files:
          keyboard = []
          for file_name, file_id, message_id in found_files:
             keyboard.append([
                 telethon.tl.types.KeyboardButtonCallback(file_name, data=f'get_file:{file_id}:{message_id}'.encode())
             ])
          await event.respond("Files found, choose one", buttons=keyboard)
       else:
          logger.info(f"No files found with name {user_input}.")
          await event.respond("No files found with that name.")

@client.on(events.CallbackQuery(data=lambda data: data.startswith(b'get_file:')))
async def get_file_handler(event):
    """Handles file selection and sends the file to the user."""
    query_data = event.data.decode().split(":")
    file_id = int(query_data[1])
    message_id = int(query_data[2])
    logger.info(f"User {event.sender_id} selected File ID {file_id}, Message ID {message_id}")
    try:
      sent_file = await send_file(event.sender_id, file_id, message_id)
    except Exception as e:
      logger.error(f"Failed to send file to user: {e}")
      await event.respond("Sorry, I could not send the file. Please try again later.")
      return
    logger.info(f"Successfully send file to user")

    # Schedule deletion after 5 minutes
    asyncio.create_task(delete_file_scheduled(event.sender_id, sent_file.id, 5*60))


async def search_file(user_input, channel_id):
    """Searches for files in the channel based on the user's input."""
    try:
        channel = await client.get_entity(channel_id)
        logger.info(f"Getting messages from channel: {channel_id}")
        all_messages = await client(GetHistoryRequest(
            peer=channel,
            limit=500,
            offset_date=None,
            offset_id=0,
            max_id=0,
            min_id=0,
            add_offset=0,
            hash=0
        ))
        logger.info(f"Successfully retrieved messages from channel.")
        found_files = []
        for message in all_messages.messages:
           if message.document:
                file_name = message.document.file_name
                if user_input.lower() in file_name.lower():
                    file_id = message.document.id
                    found_files.append((file_name, file_id, message.id))  # Store file name, id, and message ID
           if message.video:
             file_name = message.video.file_name
             if user_input.lower() in file_name.lower():
                 file_id = message.video.id
                 found_files.append((file_name, file_id, message.id))
        return found_files
    except Exception as e:
      logger.error(f"Failed to get messages from channel: {e}")
      return []


async def send_file(chat_id, file_id, message_id):
    """Sends the selected file to the user."""
    try:
      logger.info(f"Getting file message from channel with message id {message_id}")
      file_message = await client.get_messages(chat_id, ids=[message_id])
      logger.info(f"Successfully retrieved file message from channel.")
      if file_message[0].media:
          logger.info(f"Sending file {file_message[0].media}")
          sent_file = await client.send_file(chat_id, file_message[0].media)
          return sent_file
    except Exception as e:
      logger.error(f"Failed to send file to user: {e}")
      return None

async def delete_file_scheduled(chat_id, message_id, delay):
    """Deletes a file after a delay."""
    await asyncio.sleep(delay)
    await delete_file(chat_id, message_id)


async def delete_file(chat_id, message_id):
    """Deletes a message by message id."""
    try:
        logger.info(f"Deleting file with message_id: {message_id}")
        await client(DeleteMessagesRequest(
            peer=chat_id,
            id=[message_id]
            ))
        logger.info(f"File deleted successfully.")
    except Exception as e:
       logger.error(f"Error deleting file: {e}")


async def main():
    """Starts the bot."""
    logger.info("Starting bot.")
    await client.run_until_disconnected()
    logger.info("Bot Stopped.")


if __name__ == '__main__':
   asyncio.run(main())
