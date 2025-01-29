from telethon import TelegramClient, events
from config import API_ID, API_HASH, BOT_TOKEN, source_channels, destination_channel

# Initialize the bot
bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# ✅ /start command
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    await event.respond("🤖 Bot is running!\nUse `/addsource <channel_id>` to add a source channel.")

# ✅ /status command
@bot.on(events.NewMessage(pattern="/status"))
async def status(event):
    sources = source_channels.find()
    dest = destination_channel.find_one({})
    
    source_list = "\n".join([f"- {src['channel_id']}" for src in sources]) or "No source channels added."
    dest_channel = dest["channel_id"] if dest else "No destination channel set."

    await event.respond(f"📡 **Current Settings:**\n\n🔹 **Source Channels:**\n{source_list}\n\n🎯 **Destination Channel:** {dest_channel}")

# ✅ /addsource <channel_id>
@bot.on(events.NewMessage(pattern=r"/addsource (\d+)"))
async def add_source(event):
    channel_id = int(event.pattern_match.group(1))
    
    if source_channels.find_one({"channel_id": channel_id}):
        await event.respond(f"⚠️ Channel `{channel_id}` already added!")
    else:
        source_channels.insert_one({"channel_id": channel_id})
        await event.respond(f"✅ Added channel `{channel_id}` to source list.")

# ✅ /removesource <channel_id>
@bot.on(events.NewMessage(pattern=r"/removesource (\d+)"))
async def remove_source(event):
    channel_id = int(event.pattern_match.group(1))
    
    if source_channels.find_one({"channel_id": channel_id}):
        source_channels.delete_one({"channel_id": channel_id})
        await event.respond(f"✅ Removed channel `{channel_id}` from source list.")
    else:
        await event.respond(f"⚠️ Channel `{channel_id}` not found!")

# ✅ /setdestination <channel_id>
@bot.on(events.NewMessage(pattern=r"/setdestination (\d+)"))
async def set_destination(event):
    channel_id = int(event.pattern_match.group(1))
    
    destination_channel.delete_many({})
    destination_channel.insert_one({"channel_id": channel_id})
    
    await event.respond(f"🎯 Destination channel set to `{channel_id}`.")

# ✅ /startwork command
@bot.on(events.NewMessage(pattern="/startwork"))
async def start_work(event):
    await event.respond("🚀 Bot started! Now monitoring source channels for new messages.")

# ✅ /stopwork command
@bot.on(events.NewMessage(pattern="/stopwork"))
async def stop_work(event):
    await event.respond("🛑 Bot stopped! No longer monitoring messages.")

# ✅ Monitor Source Channels for New Messages
@bot.on(events.NewMessage())
async def scrape_and_post(event):
    # Check if message is from a source channel
    source = source_channels.find_one({"channel_id": event.chat_id})
    dest = destination_channel.find_one({})
    
    if source and dest:
        destination_id = dest["channel_id"]
        
        # ✅ Only copy text messages (ignore media files)
        if event.text:
            await bot.send_message(destination_id, event.text)

print("🤖 Bot Started and Monitoring Channels!")
bot.run_until_disconnected()
