from telethon import TelegramClient, events
import asyncio
import os

# Bot Token aur API Details
API_ID = '28150346'  # Replace with your API ID
API_HASH = '426f0d0a1da02dea8fb71cb0bd3ab7e1'  # Replace with your API Hash
BOT_TOKEN = '6757464190:AAG7QlwzfP3wCwyOJ_nQN9K9836RJJaZchU'  # Replace with your bot token

# Client Setup
bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Channel List Storage
channel_ids = []

# Command to Add Channels
@bot.on(events.NewMessage(pattern='/addchannel'))
async def add_channel(event):
    if event.is_private:
        try:
            channel_id = event.raw_text.split(' ')[1]
            channel_ids.append(int(channel_id))
            await event.reply(f'Channel ID {channel_id} added successfully!')
        except IndexError:
            await event.reply('Please provide a valid Channel ID. Example: /addchannel 123456789')

# Search Command
@bot.on(events.NewMessage(pattern='/search'))
async def search_files(event):
    if event.is_private:
        query = event.raw_text.split(' ', 1)[1].lower()
        found = False
        for channel_id in channel_ids:
            async for message in bot.iter_messages(channel_id, search=query):
                if message.file:
                    await event.reply('Here is the file you requested (will be deleted in 5 minutes):', file=message.file)
                    found = True
                    # Schedule file deletion
                    await asyncio.sleep(300)  # 5 minutes
                    await bot.delete_messages(event.chat_id, event.message.id)
                    break
        if not found:
            await event.reply('No files found matching your query.')

# Start the bot
print("Bot is running...")
bot.run_until_disconnected()
