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
TARGET_CHANNEL_ID = os.getenv("TARGET_CHANNEL_ID")
ALLOWED_USERS = list(map(int, os.getenv("ALLOWED_USERS", "").split(','))) if os.getenv("ALLOWED_USERS") else []

# लॉगिंग कॉन्फ़िगरेशन
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# चैनलों की सूची को स्टोर करने के लिए डिक्शनरी
source_channels = {}

async def start(update: Update, context: CallbackContext):
    """स्टार्ट कमांड के लिए हैंडलर"""
    await context.bot.send_message(chat_id=update.effective_chat.id, text="नमस्ते! मैं एक चैनल कॉपी बॉट हूँ। /addchannel, /removechannel और /listchannels जैसे कमांड का उपयोग करें।")

async def add_channel(update: Update, context: CallbackContext):
    """नया चैनल जोड़ने के लिए हैंडलर"""
    if update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("आपको यह कमांड उपयोग करने की अनुमति नहीं है।")
        return

    if len(context.args) == 0:
        await update.message.reply_text("कृपया चैनल ID डालें।")
        return

    channel_id = context.args[0]

    try:
        channel_id = int(channel_id)
        if channel_id in source_channels:
            await update.message.reply_text("चैनल पहले से ही जुड़ा हुआ है।")
            return
        source_channels[channel_id] = {'last_message_id': 0}
        await update.message.reply_text(f"चैनल {channel_id} जोड़ा गया।")

    except ValueError:
        await update.message.reply_text("चैनल ID एक मान्य पूर्णांक होना चाहिए।")


async def remove_channel(update: Update, context: CallbackContext):
    """चैनल को हटाने के लिए हैंडलर"""
    if update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("आपको यह कमांड उपयोग करने की अनुमति नहीं है।")
        return
    
    if len(context.args) == 0:
         await update.message.reply_text("कृपया चैनल ID डालें।")
         return

    channel_id = context.args[0]

    try:
        channel_id = int(channel_id)
        if channel_id in source_channels:
            del source_channels[channel_id]
            await update.message.reply_text(f"चैनल {channel_id} हटाया गया।")
        else:
            await update.message.reply_text("चैनल नहीं मिला।")
    except ValueError:
        await update.message.reply_text("चैनल ID एक मान्य पूर्णांक होना चाहिए।")


async def list_channels(update: Update, context: CallbackContext):
    """जुड़े हुए चैनलों की सूची दिखाने के लिए हैंडलर"""
    if update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("आपको यह कमांड उपयोग करने की अनुमति नहीं है।")
        return
    
    if source_channels:
        channel_list = "\n".join(str(channel_id) for channel_id in source_channels)
        await update.message.reply_text(f"जुड़े हुए चैनल:\n{channel_list}")
    else:
        await update.message.reply_text("कोई चैनल नहीं जुड़ा है।")


async def copy_message(update: Update, context: CallbackContext):
    """मैसेज को कॉपी करने के लिए हैंडलर"""

    if update.channel_post and update.channel_post.chat.id in source_channels:
        channel_id = update.channel_post.chat.id
        message = update.channel_post
        message_id = message.message_id
        if message_id > source_channels[channel_id]['last_message_id']:
             source_channels[channel_id]['last_message_id'] = message_id
             if message.text:
                text = message.text
                # लिंक हटाएं
                text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
                #टेक्स्ट मैसेज भेजें
                await context.bot.send_message(chat_id=TARGET_CHANNEL_ID, text=text)
             elif message.photo:
                 photo = message.photo[-1].file_id
                 caption = message.caption or ""
                 # लिंक हटाएं
                 caption = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', caption)
                 #फोटो और कैप्शन भेजें
                 await context.bot.send_photo(chat_id=TARGET_CHANNEL_ID, photo=photo, caption=caption)



def main():
    """मुख्य फंक्शन"""
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # कमांड हैंडलर
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('addchannel', add_channel))
    application.add_handler(CommandHandler('removechannel', remove_channel))
    application.add_handler(CommandHandler('listchannels', list_channels))

    # मैसेज हैंडलर
    application.add_handler(MessageHandler(filters.ALL, copy_message))
    
    # बॉट शुरू करें
    application.run_polling()

if __name__ == '__main__':
    main()
