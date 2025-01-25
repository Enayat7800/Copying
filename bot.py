import os
import logging
import asyncio
from telethon import TelegramClient, events, Button
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import InputPeerChannel
from pymongo import MongoClient
from urllib.parse import urlparse
import re

#logging configuration
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Environment Variables
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))
MONGO_URL = os.environ.get("MONGO_URL")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "movie_bot_db") # Default value if not provided
OWNER_ID = int(os.environ.get("OWNER_ID"))

# MongoDB Setup
mongo_client = MongoClient(MONGO_URL)
db = mongo_client[MONGO_DB_NAME]
movies_collection = db["movies"]

# Telegram Setup
bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
client = TelegramClient('client', API_ID, API_HASH)


# Function to extract movie details from post text
def extract_movie_details(text):
    match = re.match(r'(.+)\s+\((\d{4})\)\s+-\s+(.+)', text)
    if match:
        movie_name, year, quality = match.groups()
        return movie_name.strip(), year.strip(), quality.strip()
    return None, None, None

# Function to process a single post and add/update it to DB
async def process_post(post,channel):
        if post.text:
            movie_name, year, quality = extract_movie_details(post.text)
            if movie_name and year and quality:
                existing_movie = movies_collection.find_one({"movie_name": movie_name, "year": year, "quality": quality})
                file_id=None
                if post.media:
                   file_id = post.media.file.id if hasattr(post.media,'file') else None
                if existing_movie:
                    logger.info(f"Updating movie: {movie_name} ({year}) - {quality}")
                    movies_collection.update_one(
                        {"_id": existing_movie["_id"]},
                        {"$set": {"file_id": file_id, "post_id":post.id}}
                    )
                else:
                    logger.info(f"Adding movie: {movie_name} ({year}) - {quality}")
                    movies_collection.insert_one({
                        "movie_name": movie_name,
                        "year": year,
                        "quality": quality,
                         "file_id": file_id,
                         "post_id":post.id,
                         "channel_id": channel.id
                    })

# Function to fetch and process channel posts
async def fetch_and_process_posts():
    try:
        await client.connect()
        channel = await client.get_entity(CHANNEL_ID)
        offset_id = 0
        while True:
            history = await client(GetHistoryRequest(
                peer=channel,
                offset_id=offset_id,
                offset_date=None,
                add_offset=0,
                limit=100,
                max_id=0,
                min_id=0,
                hash=0
            ))
            if not history.messages:
                break
            for post in reversed(history.messages):
                await process_post(post,channel)
                offset_id = post.id

            logger.info(f"Processed {len(history.messages)} posts. Offset ID: {offset_id}")

            if len(history.messages) < 100:
                break
            
        logger.info("Initial channel scan complete.")

    except Exception as e:
          logger.error(f"Error during channel scan: {e}")
    finally:
        if client.is_connected():
             await client.disconnect()
    

# Function to get direct file URL
async def get_direct_file_url(file_id):
   try:
    async with bot:
      file = await bot.get_messages(CHANNEL_ID,ids=file_id)
      
      if not file or not file[0] or not file[0].media:
           return None
      if hasattr(file[0].media,'file') and file[0].media.file:
           return file[0].media.file.id
      else:
          return None
   except Exception as e:
       logger.error(f"Error getting direct file link: {e}")
       return None
   

# Bot Commands
@bot.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    await event.respond('Hello! Send me the name of a movie or series you want to download.')

@bot.on(events.NewMessage)
async def search_movie(event):
    query = event.message.text
    if query.startswith('/'):
        return
    
    # Search the database
    results = list(movies_collection.find({
        "$and": [
                {"channel_id": CHANNEL_ID},
                { "$or":[
            {"movie_name": {"$regex": re.compile(re.escape(query), re.IGNORECASE)}},
            {"movie_name": {"$regex": re.compile(re.escape(query), re.IGNORECASE)}},
        ]
            }
        ]
    }))

    if not results:
        await event.respond(f'Sorry, I could not find a movie or series matching "{query}". Please send your request to <a href="tg://user?id={OWNER_ID}">Support</a>',parse_mode="html")
        return

    # If there are multiple results display a list
    if len(results) > 1:
        buttons = []
        for result in results:
             movie_info = f"{result['movie_name']} ({result['year']}) - {result['quality']}"
             buttons.append(Button.inline(movie_info, data=f"select_movie_{result['_id']}"))

        await event.respond("Multiple matches found, Please select a movie:", buttons=buttons)

    elif len(results) == 1:
        await send_movie_file(event, results[0])

@bot.on(events.CallbackQuery(data=re.compile(r"select_movie_(.+)")))
async def callback_query_handler(event):
    movie_id = event.data.decode().split('_')[-1]
    result = movies_collection.find_one({"_id":movie_id})

    if result:
        await send_movie_file(event, result)
    else:
        await event.answer("Movie not found")


async def send_movie_file(event, result):
    file_id = result.get('file_id')
    post_id = result.get('post_id')
    
    if not file_id or not post_id:
        await event.respond(f"Error: No file found for {result['movie_name']}")
        return
    
    file_url = await get_direct_file_url(file_id)
    
    if not file_url:
          await event.respond(f"Error getting direct download link for {result['movie_name']}")
          return

    movie_info = f"{result['movie_name']} ({result['year']}) - {result['quality']}"
    buttons = [[Button.url('Download', url=f'https://t.me/c/{str(CHANNEL_ID)[4:]}/{post_id}?single')]]
    try:
         await bot.send_file(event.chat_id, file_url, caption=movie_info , buttons=buttons)
         
    except Exception as e:
        logger.error(f"Error sending file to user: {e}")
        await event.respond(f"Error sending file for {result['movie_name']}. Please contact support.")



async def main():
    await fetch_and_process_posts()

    # Start the bot
    try:
      await bot.run_until_disconnected()
    except Exception as e:
        logger.error(f"Error while running the bot: {e}")
    
if __name__ == '__main__':
    asyncio.run(main())
