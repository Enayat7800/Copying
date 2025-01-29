import os
import json
from pyrogram import Client, filters

# बॉट को इनिशियलाइज़ करें
app = Client(
    "ultimate_copy_bot",
    api_id=os.environ.get("API_ID"),
    api_hash=os.environ.get("API_HASH"),
    bot_token=os.environ.get("BOT_TOKEN")
)

# डेटा स्टोरेज के लिए JSON फाइल
CHANNELS_FILE = "channels.json"

# डेटा लोड करें
def load_data():
    try:
        with open(CHANNELS_FILE, "r") as f:
            data = json.load(f)
            data.setdefault("is_active", True)
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {"sources": [], "targets": [], "is_active": True}

# डेटा सेव करें
def save_data(data):
    with open(CHANNELS_FILE, "w") as f:
        json.dump(data, indent=4, ensure_ascii=False, default=str)

# /start कमांड
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    help_text = """
    🤖 **Ultimate Copy Bot Commands** 🤖

    • सोर्स ऐड करें: `/add_source चैनल_ID`
    • टारगेट ऐड करें: `/add_target चैनल_ID`
    • सोर्स रिमूव करें: `/remove_source चैनल_ID`
    • टारगेट रिमूव करें: `/remove_target चैनल_ID`
    • सभी चैनल्स देखें: `/list`
    • बॉट शुरू करें: `/start_work`
    • बॉट रोकें: `/stop_work`

    📌 चैनल ID पाने के लिए [@username_to_id_bot](https://t.me/username_to_id_bot) का इस्तेमाल करें।
    """
    await message.reply_text(help_text, disable_web_page_preview=True)

# /add_source कमांड
@app.on_message(filters.command("add_source") & filters.private)
async def add_source(client, message):
    data = load_data()
    try:
        source_id = int(message.text.split()[1])
        # पब्लिक चैनल में जॉइन करें
        try:
            await client.join_chat(source_id)
        except Exception as e:
            await message.reply(f"⚠️ चैनल में जॉइन नहीं कर पाया: {str(e)}")
            return
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
    response += f"• सोर्स: `{', '.join(map(str, data['sources']))}`\n"
    response += f"• टारगेट: `{', '.join(map(str, data['targets']))}`\n"
    response += f"• स्टेटस: `{'काम कर रहा है' if data['is_active'] else 'रुका हुआ'}`"
    await message.reply_text(response)

# /start_work और /stop_work कमांड
@app.on_message(filters.command("start_work") & filters.private)
async def start_work(client, message):
    data = load_data()
    data["is_active"] = True
    save_data(data)
    await message.reply("🚀 बॉट ने काम करना शुरू कर दिया है!")

@app.on_message(filters.command("stop_work") & filters.private)
async def stop_work(client, message):
    data = load_data()
    data["is_active"] = False
    save_data(data)
    await message.reply("🛑 बॉट ने काम रोक दिया है!")

# मैसेज कॉपी करने का लॉजिक
@app.on_message(filters.channel)
async def copy_messages(client, message):
    data = load_data()
    if not data["is_active"] or message.chat.id not in data["sources"]:
        return

    for target_id in data["targets"]:
        try:
            # टेक्स्ट मैसेज
            if message.text:
                await client.send_message(target_id, message.text)
            
            # मीडिया मैसेज
            elif message.media:
                media = message.photo or message.video or message.document or message.audio or message.sticker
                caption = message.caption if message.caption else ""
                await client.send_cached_media(
                    chat_id=target_id,
                    file_id=media.file_id,
                    caption=caption
                )
        except Exception as e:
            await message.reply(f"❌ टारगेट `{target_id}` में एरर: {str(e)}")

app.run()
