import os
from pyrogram import Client, filters

# बॉट को सेटअप करें
app = Client(
    "copy_bot",
    api_id=os.environ.get("API_ID"),
    api_hash=os.environ.get("API_HASH"),
    bot_token=os.environ.get("BOT_TOKEN")
)

# कमांड हैंडलर्स
SOURCE_CHANNEL = None
TARGET_CHANNEL = None

# /start कमांड
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text(
        "🌟 **Welcome to Copy Bot!** 🌟\n\n"
        "1. सोर्स चैनल सेट करने के लिए: `/set_source चैनल_ID`\n"
        "2. टारगेट चैनल सेट करने के लिए: `/set_target चैनल_ID`\n"
        "3. चैनल ID पाने के लिए [@username_to_id_bot](https://t.me/username_to_id_bot) का इस्तेमाल करें।"
    )

# /set_source कमांड
@app.on_message(filters.command("set_source") & filters.private)
async def set_source(client, message):
    global SOURCE_CHANNEL
    try:
        SOURCE_CHANNEL = int(message.text.split()[1])
        await message.reply(f"✅ **सोर्स चैनल ID सेट हुआ:** `{SOURCE_CHANNEL}`")
    except:
        await message.reply("❌ गलत फॉर्मेट! उदाहरण: `/set_source -1001234567890`")

# /set_target कमांड
@app.on_message(filters.command("set_target") & filters.private)
async def set_target(client, message):
    global TARGET_CHANNEL
    try:
        TARGET_CHANNEL = int(message.text.split()[1])
        await message.reply(f"✅ **टारगेट चैनल ID सेट हुआ:** `{TARGET_CHANNEL}`")
    except:
        await message.reply("❌ गलत फॉर्मेट! उदाहरण: `/set_target -1009876543210`")

# मैसेज कॉपी करने वाला लॉजिक
@app.on_message(filters.chat(SOURCE_CHANNEL) if SOURCE_CHANNEL else filters.all)
async def copy_messages(client, message):
    if not TARGET_CHANNEL:
        return
    
    try:
        # टेक्स्ट मैसेज
        if message.text:
            await client.send_message(TARGET_CHANNEL, message.text)
        
        # फोटो/वीडियो/डॉक्यूमेंट
        elif message.media:
            media = message.photo or message.video or message.document
            caption = message.caption if message.caption else ""
            await client.send_cached_media(
                chat_id=TARGET_CHANNEL,
                file_id=media.file_id,
                caption=caption
            )
    except Exception as e:
        print(f"Error: {e}")

app.run()
