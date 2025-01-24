import os
import asyncio
from telethon import TelegramClient, events
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

# Initialize bot and database
bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
mongo_client = MongoClient(MONGO_URI)
db = mongo_client['movie_search']
collection = db['movies']

# Command to add channel IDs
@bot.on(events.NewMessage(pattern="/add_channel"))
async def add_channel(event):
    if event.is_private:
        try:
            channel_id = event.message.text.split(" ", 1)[1]
            collection.update_one({"_id": "channels"}, {"$addToSet": {"ids": channel_id}}, upsert=True)
            await event.reply(f"Channel ID `{channel_id}` added successfully!")
        except IndexError:
            await event.reply("Usage: /add_channel <channel_id>")

# Search for movies
@bot.on(events.NewMessage(pattern="/search"))
async def search_movie(event):
    if event.is_private:
        query = event.message.text.split(" ", 1)[1].lower()
        channels = collection.find_one({"_id": "channels"})["ids"]
        found = False

        for channel_id in channels:
            async for message in bot.iter_messages(int(channel_id), search=query):
                if message.file:
                    await event.reply("Found this:", file=message.file)
                    found = True
                    await asyncio.sleep(300)  # 5 minutes delay
                    await message.delete()

        if not found:
            await event.reply("Sorry, no files found for your query.")

# Start the bot
print("Bot is running...")
bot.run_until_disconnected()
