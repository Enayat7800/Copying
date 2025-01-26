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
try:
    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client["MovieBot"]
    collection = db["Movies"]
    print("✅ Connected to MongoDB")
except Exception as e:
    print(f"❌ MongoDB Error: {e}")

# Pyrogram Client
app = Client("MovieBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Index Channel Movies on Startup
async def index_movies():
    try:
        # Check if Bot can access the Channel
        chat = await app.get_chat(CHANNEL_ID)
        print(f"🔄 Indexing Channel: {chat.title} (ID: {CHANNEL_ID})")

        # Fetch and index messages
        total = 0
        async for message in app.get_chat_history(CHANNEL_ID):
            if message.video or message.document:
                title = message.caption or (message.video.file_name if message.video else message.document.file_name)
                if title:
                    data = {
                        "title": title.strip().lower(),
                        "file_id": message.video.file_id if message.video else message.document.file_id
                    }
                    collection.update_one({"title": data["title"]}, {"$set": data}, upsert=True)
                    total += 1
        print(f"✅ Total {total} movies indexed!")

    except Exception as e:
        print(f"❌ INDEXING FAILED: {e}")
        print("Check 1. BOT is ADMIN in Channel 2. CHANNEL_ID is correct")

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
    try:
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
    except Exception as e:
        await message.reply(f"🚫 Error: {e}")

# Run the Bot
if __name__ == "__main__":
    print("Starting Bot...")
    try:
        app.start()
        print("Bot Started! Indexing Movies...")
        app.run(index_movies())
    except Exception as e:
        print(f"BOT START ERROR: {e}")
    finally:
        app.stop()
