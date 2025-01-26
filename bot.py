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
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # e.g., -1001234567890

# MongoDB Connection
try:
    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client["MovieBot"]
    collection = db["Movies"]
    print("✅ MongoDB Connected!")
except Exception as e:
    print(f"❌ MongoDB Error: {e}")
    exit()

# Pyrogram Client
app = Client("MovieBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def index_movies():
    try:
        # Verify Channel Access
        chat = await app.get_chat(CHANNEL_ID)
        print(f"🔄 Indexing: {chat.title}")

        # Index Movies
        count = 0
        async for msg in app.get_chat_history(CHANNEL_ID):
            if msg.video or msg.document:
                title = msg.caption or (msg.video.file_name if msg.video else msg.document.file_name)
                if title:
                    data = {
                        "title": title.strip().lower(),
                        "file_id": msg.video.file_id if msg.video else msg.document.file_id
                    }
                    collection.update_one({"title": data["title"]}, {"$set": data}, upsert=True)
                    count += 1
        print(f"✅ {count} Movies Indexed!")
    except Exception as e:
        print(f"❌ Indexing Failed: {e}")
        print("Check: 1. Bot is Admin 2. Channel ID is Correct")

async def delete_after_delay(chat_id, msg_id, delay=300):
    await asyncio.sleep(delay)
    await app.delete_messages(chat_id, msg_id)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("🎬 मूवी खोजने के लिए मुझे मूवी का नाम भेजें!")

@app.on_message(filters.private & ~filters.command("start"))
async def search(client, message):
    try:
        query = message.text.strip().lower()
        movie = collection.find_one({"title": query})
        
        if movie:
            sent_msg = await message.reply_video(movie["file_id"], caption="⚠️ यह मूवी 5 मिनट में डिलीट हो जाएगी!")
            asyncio.create_task(delete_after_delay(sent_msg.chat.id, sent_msg.id))
        else:
            await message.reply("❌ मूवी नहीं मिली!")
    except Exception as e:
        await message.reply(f"⚠️ त्रुटि: {e}")

async def main():
    print("🚀 Starting Bot...")
    try:
        await app.start()
        await index_movies()  # Index movies at startup
        await app.idle()
    except Exception as e:
        print(f"🔥 Bot Crash: {e}")
    finally:
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
