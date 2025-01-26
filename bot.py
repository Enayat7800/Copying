import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Configs
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGODB_URI = os.getenv("MONGODB_URI")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # Example: -100123456789

# MongoDB Connection
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client["MovieBot"]
collection = db["Movies"]

# Pyrogram Client
app = Client("MovieBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Index Channel Movies on Startup
async def index_movies():
    async for message in app.get_chat_history(CHANNEL_ID):
        if message.video:
            title = message.video.file_name or message.caption
            if title:
                data = {
                    "title": title.strip().lower(),
                    "file_id": message.video.file_id
                }
                collection.update_one({"title": data["title"]}, {"$set": data}, upsert=True)

# Auto-Delete Message After 5 Minutes
async def delete_after_delay(chat_id, message_id, delay=300):
    await asyncio.sleep(delay)
    await app.delete_messages(chat_id, message_id)

# Start Handler
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("Hi! Send me a movie name to search.")

# Message Handler
@app.on_message(filters.private & ~filters.command("start"))
async def search_movie(client, message: Message):
    user_query = message.text.strip().lower()
    movie_data = collection.find_one({"title": user_query})

    if movie_data:
        msg = await message.reply_video(
            movie_data["file_id"],
            caption=f"⚠️ यह मूवी 5 मिनट बाद डिलीट हो जाएगी!"
        )
        asyncio.create_task(delete_after_delay(msg.chat.id, msg.id))
    else:
        await message.reply("❌ मूवी नहीं मिली!")

# Run the Bot
if __name__ == "__main__":
    print("Indexing movies...")
    app.start()
    app.run(index_movies())
    app.stop()
