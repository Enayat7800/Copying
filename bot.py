from telethon import TelegramClient, events
import asyncio

# Bot Token aur API Details
API_ID = '28150346'  # Replace with your API ID
API_HASH = '426f0d0a1da02dea8fb71cb0bd3ab7e1'  # Replace with your API Hash
BOT_TOKEN = '6757464190:AAG7QlwzfP3wCwyOJ_nQN9K9836RJJaZchU'  # Replace with your bot token

# Client Setup
bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Channel List Storage
channel_ids = []

# /start Command
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.is_private:
        await event.reply(
            "Hi! 👋 Main ek search bot hoon.\n\n"
            "Commands:\n"
            "/addchannel <channel_id> - Add a channel for search\n"
            "Bas file ya video ka naam bhejiye, aur main usse dhoondh kar bhej dunga!"
        )

# Command to Add Channels
@bot.on(events.NewMessage(pattern='/addchannel'))
async def add_channel(event):
    if event.is_private:
        try:
            channel_id = int(event.raw_text.split(' ')[1])
            if channel_id not in channel_ids:
                channel_ids.append(channel_id)
                await event.reply(f'Channel ID {channel_id} added successfully!')
            else:
                await event.reply('This channel is already added.')
        except (IndexError, ValueError):
            await event.reply('Please provide a valid Channel ID. Example: /addchannel 123456789')

# Handle File/Video Name Directly
@bot.on(events.NewMessage)
async def handle_query(event):
    if event.is_private:
        query = event.raw_text.lower()
        found = False

        for channel_id in channel_ids:
            async for message in bot.iter_messages(channel_id, search=query):
                if message.file:  # Check if the message contains a file or video
                    await event.reply(
                        f"Here is the file you requested (will be deleted in 5 minutes):",
                        file=message.file
                    )
                    found = True
                    # Schedule file deletion after 5 minutes
                    await asyncio.sleep(300)  # 5 minutes
                    await bot.delete_messages(event.chat_id, event.message.id)
                    break

        if not found:
            await event.reply('No files or videos found matching your query.')

# Start the bot
print("Bot is running...")
bot.run_until_disconnected()
