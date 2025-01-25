import os
import asyncio
from telethon import TelegramClient, events
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Initialize Telegram client
bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# List to store channel IDs
channels = []

# Start command
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply("👋 Welcome to the Movie Search Bot!\n\nSend me a movie/series name, and I'll find it for you!")

# Add channel command
@bot.on(events.NewMessage(pattern='/addchannel'))
async def add_channel(event):
    if event.is_private:  # Ensure the command is used in private chat
        try:
            # Extract channel ID or username from the message
            command_args = event.message.text.split()
            if len(command_args) < 2:
                await event.reply("❌ Please provide the channel username or ID. Example: `/addchannel @channelusername`")
                return

            channel_id = command_args[1]
            # Save to the list
            channels.append(channel_id)
            await event.reply(f"✅ Channel `{channel_id}` has been added successfully!")
        except Exception as e:
            await event.reply(f"❌ Error adding channel: {str(e)}")

# Search functionality
@bot.on(events.NewMessage)
async def search_movie(event):
    if event.is_private and not event.message.text.startswith('/'):
        query = event.message.text.strip().lower()
        results = []

        # Search in all added channels
        for channel in channels:
            try:
                async for message in bot.iter_messages(channel, search=query):
                    if message.file:
                        results.append(message)
            except Exception as e:
                await event.reply(f"❌ Error searching in channel `{channel}`: {str(e)}")

        if results:
            # Send results to user
            for result in results:
                await event.reply(file=result.file)
            # Schedule file deletion after 5 minutes
            await asyncio.sleep(300)
            await event.delete()
        else:
            await event.reply("❌ Sorry, no results found. Please try again with a different name.")

# Run the bot
print("🤖 Bot is running...")
bot.run_until_disconnected()
