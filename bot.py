from telethon.sync import TelegramClient, events

# Replace these with your personal Telegram API credentials
API_ID = 1234567  # Replace with your API ID
API_HASH = "your_api_hash"  # Replace with your API Hash
BOT_TOKEN = "your_bot_token"  # Replace with your Bot Token

# Use client for user account
client = TelegramClient('user', API_ID, API_HASH)

async def search_in_channel(channel_username, query):
    try:
        async for message in client.iter_messages(channel_username, search=query):
            if message.file:  # Check if the message contains a file
                return message  # Return the first matching message
    except Exception as e:
        print(f"❌ Error searching in channel {channel_username}: {str(e)}")
    return None

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply("👋 Welcome to the Movie Search Bot!")

@client.on(events.NewMessage)
async def handle_search(event):
    if event.is_private:
        query = event.text.strip()
        channel_username = "@tezt3channel"  # Replace with your channel username
        result = await search_in_channel(channel_username, query)
        if result:
            await event.reply(f"🎥 Found: {result.text}", file=result.file)
        else:
            await event.reply("❌ Sorry, no results found.")

print("🤖 Bot is running...")
client.start(bot_token=BOT_TOKEN)
client.run_until_disconnected()
