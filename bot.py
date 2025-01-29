import os
import logging
from telethon import TelegramClient, events
from pymongo import MongoClient

# Enable logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables (set these in Railway's environment variables)
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
MONGO_URL = os.getenv('MONGO_URL')

# MongoDB connection
client = MongoClient(MONGO_URL)
db = client['telegram_bot']
source_channels = db['source_channels']
destination_channel = db['destination_channel']

# Initialize Telegram client
client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Command to add source channel
@client.on(events.NewMessage(pattern='/addsource'))
async def add_source_channel(event):
    channel_id = event.message.text.split(' ')[1]
    source_channels.insert_one({'channel_id': channel_id})
    await event.reply(f"Source channel {channel_id} added successfully!")

# Command to set destination channel
@client.on(events.NewMessage(pattern='/setdestination'))
async def set_destination_channel(event):
    channel_id = event.message.text.split(' ')[1]
    destination_channel.update_one({}, {'$set': {'channel_id': channel_id}}, upsert=True)
    await event.reply(f"Destination channel set to {channel_id}")

# Command to start the bot
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply("Bot is now running!")

# Command to start copying messages
@client.on(events.NewMessage(pattern='/startwork'))
async def start_work(event):
    await event.reply("Started copying messages from source channel.")
    # Start scraping messages from source channel
    while True:
        # Fetch all source channels from MongoDB
        channels = source_channels.find()
        for channel in channels:
            try:
                async for message in client.iter_messages(channel['channel_id']):
                    # Check if the message is text
                    if message.text:
                        # Send the message to destination channel
                        await client.send_message(destination_channel.find_one()['_id'], message.text)
            except Exception as e:
                logger.error(f"Error while scraping messages from channel {channel['channel_id']}: {e}")

# Command to stop copying messages
@client.on(events.NewMessage(pattern='/stopwork'))
async def stop_work(event):
    await event.reply("Stopped copying messages.")
    # Logic to stop the bot from scraping messages (could be handled by stopping the loop)

# Start the bot
client.run_until_disconnected()
