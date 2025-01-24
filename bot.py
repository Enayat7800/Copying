from telethon import TelegramClient, events
import asyncio
import os

# Environment Variables
API_ID = int(os.getenv('API_ID'))  # Railway environment me integer conversion zaroori hai
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Channel ID of your movie channel (Hardcoded here)
YOUR_MOVIE_CHANNEL_ID = -1001234567890  # Replace with your actual channel ID (including -100)

# Client Setup
bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# /start Command
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.is_private:
        await event.reply(
            "Hi! 👋 Main ek movie search bot hoon.\n\n"
            "Bas movie ka naam bhejiye, aur main usse dhoondh kar bhej dunga!\n\n"
            "Note: Yeh bot sirf specified channel se movies dhoondhega."
        )

# Handle File/Video Name Directly
@bot.on(events.NewMessage)
async def handle_query(event):
    if event.is_private:
        query = event.raw_text.lower()
        found = False

        async for message in bot.iter_messages(YOUR_MOVIE_CHANNEL_ID, search=query):
            if message.file:  # Check if the message contains a file or video
                await event.reply(
                    f"Here is the movie you requested (will be deleted in 5 minutes):",
                    file=message.file
                )
                found = True
                 # Schedule message deletion after 5 minutes
                await asyncio.sleep(300)  # 5 minutes
                await bot.delete_messages(event.chat_id, event.message.id)
                break

        if not found:
            await event.reply('No movies found matching your query.')

# Start the bot
print("Bot is running...")
bot.run_until_disconnected()
