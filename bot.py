import logging
import asyncio
from telethon import TelegramClient, events, types
from telethon.tl.functions.channels import JoinChannelRequest

# Replace with your API ID and API Hash
API_ID = "YOUR_API_ID"
API_HASH = "YOUR_API_HASH"
# Replace with your bot token
BOT_TOKEN = "YOUR_BOT_TOKEN"
# Replace with your channel id where you want to copy the messages
DESTINATION_CHANNEL_ID = "YOUR_DESTINATION_CHANNEL_ID"

# Store the channels to copy messages from
SOURCE_CHANNELS = []

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

client = TelegramClient('anon', API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def copy_message(event):
    try:
        if event.is_channel:
            await client.send_message(DESTINATION_CHANNEL_ID, event.message)
            logger.info(f"Copied message from {event.chat_id} to {DESTINATION_CHANNEL_ID}")
    except Exception as e:
        logger.error(f"Error copying message: {e}")

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond('Hi! I am your channel copier bot. Use /add_channel <channel_id> to add a source channel.')

@client.on(events.NewMessage(pattern='/add_channel'))
async def add_channel(event):
    try:
        channel_id = event.text.split(' ')[1]
        SOURCE_CHANNELS.append(channel_id)
        await event.respond(f'Channel {channel_id} added to the list of channels to copy from.')
        logger.info(f"Added channel: {channel_id}")
    except (IndexError, ValueError):
        await event.respond('Please provide a valid channel ID after the /add_channel command.')

async def main():
    await client.start(bot_token=BOT_TOKEN)
    logger.info("Bot started and is listening for messages...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
