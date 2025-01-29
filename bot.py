from telethon import TelegramClient, events
from config import API_ID, API_HASH, BOT_TOKEN, source_channels, destination_channel

bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    await event.respond("🤖 Bot is running!\nUse `/addsource <channel_id>` to add a source channel.")
    
@bot.on(events.NewMessage(pattern="/status"))
async def status(event):
    sources = source_channels.find()
    dest = destination_channel.find_one({})
    
    source_list = "\n".join([f"- {src['channel_id']}" for src in sources]) or "No source channels added."
    dest_channel = dest["channel_id"] if dest else "No destination channel set."

    await event.respond(f"📡 **Current Settings:**\n\n🔹 **Source Channels:**\n{source_list}\n\n🎯 **Destination Channel:** {dest_channel}")

print("🤖 Bot Started!")
bot.run_until_disconnected()
