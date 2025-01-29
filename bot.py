import os
import json
from pyrogram import Client, filters

# बॉट को इनिशियलाइज़ करें
app = Client(
    "advance_copy_bot",
    api_id=os.environ.get("API_ID"),
    api_hash=os.environ.get("API_HASH"),
    bot_token=os.environ.get("BOT_TOKEN")
)

# Channel Data को स्टोर करने के लिए JSON फाइल
CHANNELS_FILE = "channels.json"

# JSON से डेटा लोड करें
def load_data():
    try:
        with open(CHANNELS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"sources": [], "targets": []}

# JSON में डेटा सेव करें
def save_data(data):
    with open(CHANNELS_FILE, "w") as f:
        json.dump(data, f)

# /start कमांड
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    help_text = """
    🚀 **Advance Copy Bot Commands** 🚀

    • सोर्स चैनल ऐड करें: `/add_source चैनल_ID`
    • टारगेट चैनल ऐड करें: `/add_target चैनल_ID`
    • सोर्स चैनल रिमूव करें: `/remove_source चैनल_ID`
    • टारगेट चैनल रिमूव करें: `/remove_target चैनल_ID`
    • सभी चैनल्स देखें: `/list`

    📝 चैनल ID पाने के लिए [@username_to_id_bot](https://t.me/username_to_id_bot) का इस्तेमाल करें।
    """
    await message.reply_text(help_text)

# /add_source कमांड
@app.on_message(filters.command("add_source") & filters.private)
async def add_source(client, message):
    data = load_data()
    try:
        source_id = int(message.text.split()[1])
        if source_id not in data["sources"]:
            data["sources"].append(source_id)
            save_data(data)
            await message.reply(f"✅ **सोर्स ऐड हुआ:** `{source_id}`")
        else:
            await message.reply("⚠️ यह सोर्स पहले से ऐड है!")
    except:
        await message.reply("❌ गलत फॉर्मेट! उदाहरण: `/add_source -1001234567890`")

# /add_target कमांड
@app.on_message(filters.command("add_target") & filters.private)
async def add_target(client, message):
    data = load_data()
    try:
        target_id = int(message.text.split()[1])
        if target_id not in data["targets"]:
            data["targets"].append(target_id)
            save_data(data)
            await message.reply(f"✅ **टारगेट ऐड हुआ:** `{target_id}`")
        else:
            await message.reply("⚠️ यह टारगेट पहले से ऐड है!")
    except:
        await message.reply("❌ गलत फॉर्मेट! उदाहरण: `/add_target -1009876543210`")

# /remove_source कमांड
@app.on_message(filters.command("remove_source") & filters.private)
async def remove_source(client, message):
    data = load_data()
    try:
        source_id = int(message.text.split()[1])
        if source_id in data["sources"]:
            data["sources"].remove(source_id)
            save_data(data)
            await message.reply(f"🗑️ **सोर्स रिमूव हुआ:** `{source_id}`")
        else:
            await message.reply("❌ यह सोर्स ऐड नहीं है!")
    except:
        await message.reply("❌ गलत फॉर्मेट! उदाहरण: `/remove_source -1001234567890`")

# /remove_target कमांड
@app.on_message(filters.command("remove_target") & filters.private)
async def remove_target(client, message):
    data = load_data()
    try:
        target_id = int(message.text.split()[1])
        if target_id in data["targets"]:
            data["targets"].remove(target_id)
            save_data(data)
            await message.reply(f"🗑️ **टारगेट रिमूव हुआ:** `{target_id}`")
        else:
            await message.reply("❌ यह टारगेट ऐड नहीं है!")
    except:
        await message.reply("❌ गलत फॉर्मेट! उदाहरण: `/remove_target -1009876543210`")

# /list कमांड
@app.on_message(filters.command("list") & filters.private)
async def list_channels(client, message):
    data = load_data()
    response = "📜 **चैनल्स की लिस्ट:**\n\n"
    response += f"• **सोर्स चैनल्स:**\n{', '.join(map(str, data['sources']))}\n\n"
    response += f"• **टारगेट चैनल्स:**\n{', '.join(map(str, data['targets']))}"
    await message.reply_text(response)

# मैसेज कॉपी करने का लॉजिक
@app.on_message(filters.channel)
async def copy_messages(client, message):
    data = load_data()
    if message.chat.id in data["sources"] and data["targets"]:
        for target_id in data["targets"]:
            try:
                # टेक्स्ट मैसेज
                if message.text:
                    await client.send_message(target_id, message.text)
                
                # मीडिया मैसेज (फोटो, वीडियो, ऑडियो, स्टिकर, डॉक्यूमेंट)
                elif message.media:
                    media = message.photo or message.video or message.audio or message.sticker or message.document
                    caption = message.caption if message.caption else ""
                    await client.send_cached_media(
                        chat_id=target_id,
                        file_id=media.file_id,
                        caption=caption
                    )
            except Exception as e:
                print(f"Error in target {target_id}: {e}")

app.run()
