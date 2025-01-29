import logging
import os
import re
import asyncio
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext

# पर्यावरण चर को लोड करना
from dotenv import load_dotenv
load_dotenv()

# बोट टोकन और चैनल आईडी को पर्यावरण चर से लेना
BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USERS = list(map(int, os.getenv("ALLOWED_USERS", "").split(','))) if os.getenv("ALLOWED_USERS") else []

# लॉगिंग कॉन्फ़िगरेशन
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# चैनलों की सूची को स्टोर करने के लिए डिक्शनरी
source_channels = {}
target_channel_id = None  # Initialize target_channel_id to None

async def start(update: Update, context: CallbackContext):
    """स्टार्ट कमांड के लिए हैंडलर"""
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                    text="नमस्ते! मैं एक चैनल कॉपी बॉट हूँ। /addchannel, /removechannel, /listchannels, /settarget और /showtarget जैसे कमांड का उपयोग करें।")


async def add_channel(update: Update, context: CallbackContext):
    """नया चैनल जोड़ने के लिए हैंडलर"""
    if ALLOWED_USERS and update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("आपको यह कमांड उपयोग करने की अनुमति नहीं है।")
        return

    if len(context.args) == 0:
        await update.message.reply_text("कृपया चैनल ID डालें।\nउदाहरण: `/addchannel -1001234567890`")
        return

    channel_id = context.args[0]

    try:
        channel_id = int(channel_id)
        if channel_id in source_channels:
            await update.message.reply_text("चैनल पहले से ही जुड़ा हुआ है।")
            return
        source_channels[channel_id] = {'last_message_id': 0}
        await update.message.reply_text(f"चैनल {channel_id} जोड़ा गया।")
        logging.info(f"Channel {channel_id} added.")

    except ValueError:
        await update.message.reply_text("चैनल ID एक मान्य पूर्णांक होना चाहिए।\nउदाहरण: `/addchannel -1001234567890`")
        logging.warning(f"Invalid channel ID format: {channel_id}")


async def remove_channel(update: Update, context: CallbackContext):
    """चैनल को हटाने के लिए हैंडलर"""
    if ALLOWED_USERS and update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("आपको यह कमांड उपयोग करने की अनुमति नहीं है।")
        return
    
    if len(context.args) == 0:
         await update.message.reply_text("कृपया चैनल ID डालें।\nउदाहरण: `/removechannel -1001234567890`")
         return

    channel_id = context.args[0]

    try:
        channel_id = int(channel_id)
        if channel_id in source_channels:
            del source_channels[channel_id]
            await update.message.reply_text(f"चैनल {channel_id} हटाया गया।")
            logging.info(f"Channel {channel_id} removed.")

        else:
            await update.message.reply_text("चैनल नहीं मिला।")
            logging.warning(f"Channel {channel_id} not found.")
    except ValueError:
         await update.message.reply_text("चैनल ID एक मान्य पूर्णांक होना चाहिए।\nउदाहरण: `/removechannel -1001234567890`")
         logging.warning(f"Invalid channel ID format: {channel_id}")


async def list_channels(update: Update, context: CallbackContext):
    """जुड़े हुए चैनलों की सूची दिखाने के लिए हैंडलर"""
    if ALLOWED_USERS and update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("आपको यह कमांड उपयोग करने की अनुमति नहीं है।")
        return
    
    if source_channels:
        channel_list = "\n".join(str(channel_id) for channel_id in source_channels)
        await update.message.reply_text(f"जुड़े हुए चैनल:\n{channel_list}")
        logging.info(f"List of channels: {channel_list}")

    else:
        await update.message.reply_text("कोई चैनल नहीं जुड़ा है।")
        logging.info("No channels connected.")


async def set_target(update: Update, context: CallbackContext):
    """टारगेट चैनल सेट करने के लिए हैंडलर"""
    global target_channel_id
    if ALLOWED_USERS and update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("आपको यह कमांड उपयोग करने की अनुमति नहीं है।")
        return
    
    if len(context.args) == 0:
        await update.message.reply_text("कृपया टारगेट चैनल ID डालें।\nउदाहरण: `/settarget -1001234567890`")
        return
    
    channel_id = context.args[0]
    try:
      channel_id = int(channel_id)
      target_channel_id = channel_id
      await update.message.reply_text(f"टारगेट चैनल {channel_id} सेट किया गया।")
      logging.info(f"Target channel set to: {target_channel_id}")

    except ValueError:
         await update.message.reply_text("टारगेट चैनल ID एक मान्य पूर्णांक होना चाहिए।\nउदाहरण: `/settarget -1001234567890`")
         logging.warning(f"Invalid target channel ID format: {channel_id}")


async def show_target(update: Update, context: CallbackContext):
    """सेट किए हुए टारगेट चैनल को दिखाने के लिए हैंडलर"""
    if ALLOWED_USERS and update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("आपको यह कमांड उपयोग करने की अनुमति नहीं है।")
        return

    if target_channel_id:
        await update.message.reply_text(f"टारगेट चैनल ID: {target_channel_id}")
        logging.info(f"Current target channel: {target_channel_id}")

    else:
        await update.message.reply_text("कोई टारगेट चैनल सेट नहीं है। कृपया `/settarget` कमांड का उपयोग करें।")
        logging.info("No target channel set.")


async def copy_message(update: Update, context: CallbackContext):
    """मैसेज को कॉपी करने के लिए हैंडलर"""
    global target_channel_id
    
    if target_channel_id is None:
        logging.info("No target channel is set.")
        return

    if update.channel_post and update.channel_post.chat.id in source_channels:
        channel_id = update.channel_post.chat.id
        message = update.channel_post
        message_id = message.message_id

        logging.info(f"Message from channel {channel_id}, message_id: {message_id}")

        if message_id > source_channels[channel_id]['last_message_id']:
            source_channels[channel_id]['last_message_id'] = message_id
            logging.info(f"Processing new message from channel {channel_id}")
            
            if message.text:
                text = message.text
                # लिंक हटाएं
                text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
                 #टेक्स्ट मैसेज भेजें
                await context.bot.send_message(chat_id=target_channel_id, text=text)
                logging.info(f"Message sent to target channel: {target_channel_id}")


            elif message.photo:
                photo = message.photo[-1].file_id
                caption = message.caption or ""
                 # लिंक हटाएं
                caption = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', caption)
                #फोटो और कैप्शन भेजें
                await context.bot.send_photo(chat_id=target_channel_id, photo=photo, caption=caption)
                logging.info(f"Photo sent to target channel: {target_channel_id}")



def main():
    """मुख्य फंक्शन"""
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # कमांड हैंडलर
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('addchannel', add_channel))
    application.add_handler(CommandHandler('removechannel', remove_channel))
    application.add_handler(CommandHandler('listchannels', list_channels))
    application.add_handler(CommandHandler('settarget', set_target))
    application.add_handler(CommandHandler('showtarget', show_target))

    # मैसेज हैंडलर
    application.add_handler(MessageHandler(filters.ALL, copy_message))
    
    # बॉट शुरू करें
    application.run_polling()

if __name__ == '__main__':
    main()
