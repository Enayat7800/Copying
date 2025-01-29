import os
import time
import logging
import asyncio
import re
from pyrogram import Client, filters
from pyrogram.types import Message

# टेलीग्राम बॉट टोकन और एपीआई आईडी (अपने क्रेडेंशियल से बदलें)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
# डेस्टिनेशन चैनल को एनवायरनमेंट वेरिएबल से लें
DESTINATION_CHANNEL = os.environ.get("DESTINATION_CHANNEL")

# सोर्स चैनलों की सूची (इसे डेटाबेस या फाइल में भी स्टोर किया जा सकता है)
source_channels = []

# लॉगिंग सेटअप
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# बॉट क्लाइंट
app = Client("message_copier_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


# फंक्शन: टेक्स्ट से लिंक हटाता है
def remove_links(text):
    if text:
        return re.sub(r'http\S+|www.\S+', '', text)
    else:
        return ""

# कमांड: /start
@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    await message.reply_text("बॉट शुरू हो गया है! /startwork कमांड से मैसेज कॉपी करना शुरू करें।")


# कमांड: /stop
@app.on_message(filters.command("stop"))
async def stop_command(client: Client, message: Message):
     global is_working
     is_working = False
     await message.reply_text("बॉट बंद हो गया है।")

# कमांड: /startwork
@app.on_message(filters.command("startwork"))
async def startwork_command(client: Client, message: Message):
    global is_working
    is_working = True
    await message.reply_text("मैसेज कॉपी करना शुरू हो गया है।")

# कमांड: /stopwork
@app.on_message(filters.command("stopwork"))
async def stopwork_command(client: Client, message: Message):
    global is_working
    is_working = False
    await message.reply_text("मैसेज कॉपी करना बंद हो गया है।")


# कमांड: /addchannel
@app.on_message(filters.command("addchannel"))
async def add_channel(client: Client, message: Message):
    if len(message.command) != 2:
         await message.reply_text("कृपया चैनल का username प्रदान करें। उदाहरण: `/addchannel channel_username`")
         return
    channel_username = message.command[1]
    if channel_username.startswith('@'):
        channel_username = channel_username[1:]
    if channel_username not in source_channels:
        source_channels.append(channel_username)
        await message.reply_text(f"चैनल @{channel_username} जोड़ा गया।")
    else:
         await message.reply_text("यह चैनल पहले से ही सूची में है।")
        

# कमांड: /removechannel
@app.on_message(filters.command("removechannel"))
async def remove_channel(client: Client, message: Message):
    if len(message.command) != 2:
        await message.reply_text("कृपया चैनल का username प्रदान करें। उदाहरण: `/removechannel channel_username`")
        return
    channel_username = message.command[1]
    if channel_username.startswith('@'):
        channel_username = channel_username[1:]
    if channel_username in source_channels:
        source_channels.remove(channel_username)
        await message.reply_text(f"चैनल @{channel_username} हटाया गया।")
    else:
        await message.reply_text("यह चैनल सूची में नहीं है।")

# कमांड: /listchannels
@app.on_message(filters.command("listchannels"))
async def list_channels(client: Client, message: Message):
    if source_channels:
         channels_list = "\n".join(f"@{channel}" for channel in source_channels)
         await message.reply_text(f"स्रोत चैनल:\n{channels_list}")
    else:
         await message.reply_text("कोई स्रोत चैनल नहीं हैं।")

# कमांड: /setdestination
@app.on_message(filters.command("setdestination"))
async def set_destination_channel(client: Client, message: Message):
    global DESTINATION_CHANNEL
    if len(message.command) != 2:
        await message.reply_text("कृपया डेस्टिनेशन चैनल का username प्रदान करें। उदाहरण: `/setdestination channel_username`")
        return
    
    new_destination_channel = message.command[1]
    if new_destination_channel.startswith('@'):
        new_destination_channel = new_destination_channel[1:]
    
    DESTINATION_CHANNEL = new_destination_channel
    os.environ["DESTINATION_CHANNEL"] = new_destination_channel
    await message.reply_text(f"डेस्टिनेशन चैनल @{new_destination_channel} पर सेट किया गया है।")

# मैसेज कॉपी करने का लूप
async def copy_messages():
    global is_working
    while True:
        try:
            if is_working:
                now = time.localtime()
                current_hour = now.tm_hour
                if 8 <= current_hour < 22:
                    for channel_username in source_channels:
                        async for message in app.get_chat_history(channel_username, limit=5):
                            if message.text:
                                try:
                                        cleaned_text = remove_links(message.text)
                                        await app.send_message(DESTINATION_CHANNEL, cleaned_text)
                                        logger.info(f"मैसेज को चैनल @{channel_username} से @{DESTINATION_CHANNEL} में कॉपी किया गया: {cleaned_text[:50]}...")
                                except Exception as e:
                                    logger.error(f"मैसेज कॉपी करने में त्रुटि: {e}")
                            elif message.photo:
                                    try:
                                        await app.send_photo(DESTINATION_CHANNEL, message.photo.file_id , caption=remove_links(message.caption))
                                        logger.info(f"फोटो को चैनल @{channel_username} से @{DESTINATION_CHANNEL} में कॉपी किया गया।")
                                    except Exception as e:
                                         logger.error(f"फोटो कॉपी करने में त्रुटि: {e}")

                                else:
                                    logger.info(f"मैसेज को छोड़ा गया @{channel_username} मैसेज में टेक्स्ट या फोटो नहीं था ")


                    await asyncio.sleep(60)  # हर मिनट मैसेज चेक करे
                else:
                    logger.info("बॉट कार्य समय के बाहर है (सुबह 8 बजे से रात 10 बजे तक)।")
                    await asyncio.sleep(3600)  # हर घंटे चेक करे
            else:
                 await asyncio.sleep(60) # हर मिनट चेक करे
        except Exception as e:
            logger.error(f"मुख्य लूप में त्रुटि: {e}")
            await asyncio.sleep(60)

# बॉट को रन करें
async def main():
     await asyncio.gather(app.start(),copy_messages())

if __name__ == "__main__":
    asyncio.run(main())
