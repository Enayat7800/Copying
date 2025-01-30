from telethon import TelegramClient, events

# API details
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
bot_token = os.environ.get("BOT_TOKEN")

# Source and destination channel IDs
source_channel_id = int(os.environ.get("SOURCE_CHANNEL_ID"))
destination_channel_id = int(os.environ.get("DESTINATION_CHANNEL_ID"))

# Create client
client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# Start command handler
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply('Bot shuru ho gaya hai!')

# Message handler
@client.on(events.NewMessage(chats=source_channel_id))
async def message(event):
    message = event.message
    await client.send_message(destination_channel_id, message)

# Run the bot
client.run_until_disconnected()
