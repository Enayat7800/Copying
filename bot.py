import os
import json
from telethon import TelegramClient, events, types
from datetime import datetime, timedelta
import logging
import re
from pymongo import MongoClient

# Environment variables
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
NOTIFICATION_CHANNEL_ID = int(os.getenv('NOTIFICATION_CHANNEL_ID'))

# MongoDB URL from environment variable
MONGO_URL = os.getenv('MONGO_URL')

# MongoDB client
try:
    client_mongo = MongoClient(MONGO_URL)
    db = client_mongo.get_default_database() # get database name from URL
    bot_data_collection = db['bot_data'] # collection for bot data
    logging.info(f"Connected to MongoDB!")
except Exception as e:
    logging.error(f"Error connecting to MongoDB: {e}")
    client_mongo = None # to avoid using mongo client further

# Initialize the client
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Set up logging
logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def send_notification(message):
    """Sends a message to the specified notification channel."""
    try:
        await client.send_message(NOTIFICATION_CHANNEL_ID, message)
        logging.info(f"Notification sent to channel {NOTIFICATION_CHANNEL_ID}: {message}")
    except Exception as e:
        logging.error(f"Error sending notification: {e}")

def is_trial_active(user_id):
    user_data = load_data()[2]
    if user_id in user_data:
        start_date = datetime.fromisoformat(user_data[user_id]['start_date'])
        trial_end_date = start_date + timedelta(days=3)
        return datetime.now() <= trial_end_date, False
    return True, True

def is_user_active(user_id):
    user_data = load_data()[2]
    if user_id in user_data:
        if user_data[user_id].get('is_paid',False):
            start_date = datetime.fromisoformat(user_data[user_id]['start_date'])
            end_date = start_date + timedelta(days=30)
            return datetime.now() <= end_date
        else:
             return is_trial_active(user_id)[0]
    else:
         return is_trial_active(user_id)[0]
    
def check_user_status(user_id):
    user_data = load_data()[2]
    if user_id in user_data:
        if user_data[user_id].get('is_blocked',False):
            return False
        else:
            return is_user_active(user_id)
    else:
        return is_trial_active(user_id)[0]
    
# Load data from MongoDB
def load_data():
    if client_mongo:
         bot_data = bot_data_collection.find_one()
         if bot_data:
            return (
                bot_data.get('channel_ids', []),
                bot_data.get('text_links', {}),
                bot_data.get('user_data', {}),
                bot_data.get('copy_data', {})
            )
    return [], {}, {}, {}

# Save data to MongoDB
def save_data(channel_ids, text_links, user_data, copy_data):
    if client_mongo:
       data = {
           'channel_ids': channel_ids,
           'text_links': text_links,
           'user_data': user_data,
           'copy_data': copy_data
       }
       bot_data_collection.replace_one({}, data, upsert=True)

# Initialize the bot with data from storage
CHANNEL_IDS, text_links, user_data, copy_data = load_data()

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    logging.info(f"User ID {user_id} used /start command.")

    if not check_user_status(user_id):
       await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
       return
    
    user_data = load_data()[2]
    is_new_user = user_id not in user_data
    if is_new_user:
       user_data[user_id] = {
        'start_date': datetime.now().isoformat(),
        'is_paid':False,
        'is_blocked':False
        }
       save_data(load_data()[0], load_data()[1], user_data, load_data()[3])
       user = await client.get_entity(user_id)
       username = user.username if user.username else "N/A"
       await send_notification(f"New user started the bot:\nUser ID: {user_id}\nUsername: @{username}")

    await event.respond('Namaste! 🙏 Captain Bot mein aapka swagat hai!\n\n'
                        'Ye bot aapke messages mein automatically links add kar dega aur channel se message copy kar ke aapke channel pe bhi post kar dega.\n\n'
                        'Agar aapko koi problem ho ya help chahiye, to /help command use karein.\n\n')

@client.on(events.NewMessage(pattern='/help'))
async def help(event):
    if not check_user_status(event.sender_id):
       await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
       return
    help_message = (
        "Bot commands:\n\n"
        "/start - Bot ko shuru karein\n"
        "/help - Commands aur contact information dekhen\n"
        "/addchannel - Channel add karein (jaise: /addchannel -100123456789)\n"
        "/addlink - Text aur link add karein (jaise: /addlink text link)\n"
        "/showchannels - Added channels dekhein\n"
        "/showlinks - Added links dekhein\n"
        "/removechannel - Channel remove karein (jaise: /removechannel -100123456789)\n"
        "/removelink - Link remove karein (jaise: /removelink text)\n"
        "/addcopy - Message copying set karein (jaise: /addcopy source_channel_id destination_channel_id)\n"
        "/removecopy - Message copying remove karein (jaise: /removecopy source_channel_id)\n\n"
        "Contact for help: @captain_stive"
    )
    await event.respond(help_message)

@client.on(events.NewMessage(pattern=r'/addchannel'))
async def add_channel(event):
    if not check_user_status(event.sender_id):
        await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
        return

    full_command = event.text.strip()
    match = re.match(r'/addchannel (-?\d+)', full_command)
    if not match:
        await event.respond('Invalid command format. Use: /addchannel -100123456789')
        return
    CHANNEL_IDS = load_data()[0]
    try:
        channel_id = int(match.group(1))
        if channel_id not in CHANNEL_IDS:
            CHANNEL_IDS.append(channel_id)
            save_data(CHANNEL_IDS, load_data()[1], load_data()[2], load_data()[3])
            await event.respond(f'Channel ID {channel_id} add ho gaya! 👍')
            await send_notification(f"Channel added by user {event.sender_id}:\nChannel ID: {channel_id}")
        else:
            await event.respond(f'Channel ID {channel_id} pahle se hi add hai! ⚠️')
    except ValueError:
        await event.respond('Invalid channel ID. Please use a valid integer.')
    logging.info(f"Current CHANNEL_IDS: {CHANNEL_IDS}")

@client.on(events.NewMessage(pattern=r'/addlink'))
async def add_link(event):
    if not check_user_status(event.sender_id):
         await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
         return
    full_command = event.text.strip()
    match = re.match(r'/addlink (.+) (https?://[^\s]+)', full_command)
    if not match:
        await event.respond('Invalid command format. Use: /addlink text link (eg: /addlink mytext https://example.com)')
        return

    text = match.group(1).strip()
    link = match.group(2)
    text_links = load_data()[1]
    text_links[text] = link
    save_data(load_data()[0], text_links, load_data()[2], load_data()[3])
    await event.respond(f'Text "{text}" aur link "{link}" add ho gaya! 👍')
    await send_notification(f"Link added by user {event.sender_id}:\nText: {text}\nLink: {link}")
    logging.info(f"Current text_links: {text_links}")

@client.on(events.NewMessage(pattern='/showchannels'))
async def show_channels(event):
    if not check_user_status(event.sender_id):
        await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
        return
    CHANNEL_IDS = load_data()[0]
    if CHANNEL_IDS:
        channel_list = "\n".join([str(cid) for cid in CHANNEL_IDS])
        await event.respond(f'Current monitored channels:\n{channel_list}')
    else:
        await event.respond('No channels added yet.')
    logging.info(f"Current CHANNEL_IDS: {CHANNEL_IDS}")

@client.on(events.NewMessage(pattern='/showlinks'))
async def show_links(event):
    if not check_user_status(event.sender_id):
         await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
         return
    text_links = load_data()[1]
    if text_links:
        link_list = "\n".join([f'{text}: {link}' for text, link in text_links.items()])
        await event.respond(f'Current links:\n{link_list}')
    else:
        await event.respond('No links added yet.')
    logging.info(f"Current text_links: {text_links}")

@client.on(events.NewMessage(pattern=r'/removechannel'))
async def remove_channel(event):
    if not check_user_status(event.sender_id):
         await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
         return
    full_command = event.text.strip()
    match = re.match(r'/removechannel (-?\d+)', full_command)
    if not match:
        await event.respond('Invalid command format. Use: /removechannel -100123456789')
        return

    try:
        channel_id = int(match.group(1))
        CHANNEL_IDS = load_data()[0]
        if channel_id in CHANNEL_IDS:
            CHANNEL_IDS.remove(channel_id)
            save_data(CHANNEL_IDS, load_data()[1], load_data()[2], load_data()[3])
            await event.respond(f'Channel ID {channel_id} removed! 👍')
        else:
             await event.respond(f'Channel ID {channel_id} not found! ⚠️')
    except ValueError:
            await event.respond('Invalid channel ID. Please use a valid integer.')
    logging.info(f"Current CHANNEL_IDS: {load_data()[0]}")

@client.on(events.NewMessage(pattern=r'/removelink'))
async def remove_link(event):
    if not check_user_status(event.sender_id):
        await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
        return

    full_command = event.text.strip()
    match = re.match(r'/removelink (.+)', full_command)
    if not match:
        await event.respond('Invalid command format. Use: /removelink text (eg: /removelink mytext)')
        return
        
    text = match.group(1).strip()
    text_links = load_data()[1]
    if text in text_links:
        del text_links[text]
        save_data(load_data()[0], text_links, load_data()[2], load_data()[3])
        await event.respond(f'Link with text "{text}" removed! 👍')
    else:
         await event.respond(f'Link with text "{text}" not found! ⚠️')
    logging.info(f"Current text_links: {load_data()[1]}")

@client.on(events.NewMessage(pattern=r'/adminactivate'))
async def activate_user(event):
    if event.sender_id != ADMIN_ID:
        await event.respond("You are not authorized to use this command.")
        return
    
    if event.sender_id != event.chat_id:
        await event.respond("This command should be used in a private chat with the bot.")
        return
    
    full_command = event.text.strip()
    match = re.match(r'/adminactivate (-?\d+)', full_command)
    if not match:
        await event.respond('Invalid command format. Use: /adminactivate <user_id>')
        return
        
    try:
        user_id_to_activate = int(match.group(1))
        user_data = load_data()[2]
        if user_id_to_activate in user_data:
            user_data[user_id_to_activate]['start_date'] = datetime.now().isoformat()
            user_data[user_id_to_activate]['is_paid'] = True
            user_data[user_id_to_activate]['is_blocked'] = False
            save_data(load_data()[0], load_data()[1], user_data, load_data()[3])
            await event.respond(f'User ID {user_id_to_activate} activated for 30 days! ✅')
            await client.send_message(user_id_to_activate, "Congratulations! Your account has been activated for 30 days. Enjoy using the bot!")
        else:
             await event.respond(f'User ID {user_id_to_activate} not found! ⚠️')
    except ValueError:
       await event.respond('Invalid user ID. Please use a valid integer.')

@client.on(events.NewMessage(pattern=r'/adminblock'))
async def block_user(event):
    if event.sender_id != ADMIN_ID:
        await event.respond("You are not authorized to use this command.")
        return
    
    if event.sender_id != event.chat_id:
        await event.respond("This command should be used in a private chat with the bot.")
        return
    
    full_command = event.text.strip()
    match = re.match(r'/adminblock (-?\d+)', full_command)
    if not match:
        await event.respond('Invalid command format. Use: /adminblock <user_id>')
        return
        
    try:
        user_id_to_block = int(match.group(1))
        user_data = load_data()[2]
        if user_id_to_block in user_data:
            user_data[user_id_to_block]['is_blocked'] = True
            save_data(load_data()[0], load_data()[1], user_data, load_data()[3])
            await event.respond(f'User ID {user_id_to_block} blocked! 🚫')
        else:
             await event.respond(f'User ID {user_id_to_block} not found! ⚠️')
    except ValueError:
       await event.respond('Invalid user ID. Please use a valid integer.')
    
@client.on(events.NewMessage(pattern=r'/adminunblock'))
async def unblock_user(event):
    if event.sender_id != ADMIN_ID:
        await event.respond("You are not authorized to use this command.")
        return
    
    if event.sender_id != event.chat_id:
        await event.respond("This command should be used in a private chat with the bot.")
        return
    
    full_command = event.text.strip()
    match = re.match(r'/adminunblock (-?\d+)', full_command)
    if not match:
        await event.respond('Invalid command format. Use: /adminunblock <user_id>')
        return
    
    try:
        user_id_to_unblock = int(match.group(1))
        user_data = load_data()[2]
        if user_id_to_unblock in user_data:
            user_data[user_id_to_unblock]['is_blocked'] = False
            save_data(load_data()[0], load_data()[1], user_data, load_data()[3])
            await event.respond(f'User ID {user_id_to_unblock} unblocked! ✅')
        else:
             await event.respond(f'User ID {user_id_to_unblock} not found! ⚠️')
    except ValueError:
       await event.respond('Invalid user ID. Please use a valid integer.')
    
@client.on(events.ChatAction)
async def handle_chat_actions(event):
    if event.user_added and event.who == await client.get_me():
       try:
            chat = await client.get_entity(event.chat_id)
            if chat.username:
               await send_notification(f"Bot added to channel: @{chat.username}")
            else:
               await send_notification(f"Bot added to channel: {chat.title}")
       except Exception as e:
            logging.error(f"Error getting chat username: {e}")


@client.on(events.NewMessage(pattern=r'/addcopy'))
async def add_copy(event):
    if not check_user_status(event.sender_id):
        await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
        return
    
    full_command = event.text.strip()
    match = re.match(r'/addcopy (-?\d+) (-?\d+)', full_command)
    if not match:
        await event.respond('Invalid command format. Use: /addcopy source_channel_id destination_channel_id')
        return

    try:
        source_channel_id = int(match.group(1))
        destination_channel_id = int(match.group(2))
        
        copy_data = load_data()[3]
        if str(source_channel_id) not in copy_data:
           copy_data[str(source_channel_id)] = destination_channel_id
           save_data(load_data()[0], load_data()[1], load_data()[2], copy_data)
           await event.respond(f'Messages from channel {source_channel_id} will now be copied to {destination_channel_id} 👍')
           await send_notification(f"Copying set by user {event.sender_id}:\nSource: {source_channel_id}\nDestination: {destination_channel_id}")
        else:
            await event.respond(f'Copying from {source_channel_id} already set. ⚠️')
    except ValueError:
           await event.respond('Invalid channel ID. Please use a valid integer.')
    logging.info(f"Current copy_data: {load_data()[3]}")

@client.on(events.NewMessage(pattern=r'/removecopy'))
async def remove_copy(event):
   if not check_user_status(event.sender_id):
        await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
        return
   
   full_command = event.text.strip()
   match = re.match(r'/removecopy (-?\d+)', full_command)
   if not match:
        await event.respond('Invalid command format. Use: /removecopy source_channel_id')
        return

   try:
        source_channel_id = int(match.group(1))
        copy_data = load_data()[3]
        if str(source_channel_id) in copy_data:
            del copy_data[str(source_channel_id)]
            save_data(load_data()[0], load_data()[1], load_data()[2], copy_data)
            await event.respond(f'Copying from {source_channel_id} removed! 👍')
            await send_notification(f"Copying removed by user {event.sender_id}:\nSource: {source_channel_id}")
        else:
            await event.respond(f'Copying from {source_channel_id} not found! ⚠️')
   except ValueError:
        await event.respond('Invalid channel ID. Please use a valid integer.')
   logging.info(f"Current copy_data: {load_data()[3]}")

@client.on(events.NewMessage())
async def add_links(event):
    user_id = event.sender_id
    if not check_user_status(user_id):
        if event.is_private:
            await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
        return
    
    CHANNEL_IDS = load_data()[0]
    if event.is_channel and event.chat_id in CHANNEL_IDS:
        logging.info(f"Message received from channel ID: {event.chat_id}")
        message_text = event.message.message if event.message.message else ""
        
        # Handle media messages
        if event.message.media:
            caption = event.message.message or ""  # Use caption as message
            modified_caption = caption
            
            text_links = load_data()[1]
            for text, link in text_links.items():
                if text in modified_caption:
                     modified_caption = modified_caption.replace(text, f"{text}\n{link}")
            if modified_caption != caption:
              try:
                   await event.edit(text=modified_caption, file=event.message.media)
                   logging.info(f"Edited media message caption in channel ID: {event.chat_id}")
              except Exception as e:
                    logging.error(f"Error editing media message caption in channel {event.chat_id}: {e}")
        else:
           # Handle text messages
           if message_text:
               modified_text = message_text
               text_links = load_data()[1]
               for text, link in text_links.items():
                    if text in modified_text:
                         modified_text = modified_text.replace(text,f"{text}\n{link}")
               if modified_text != message_text:
                   try:
                        await event.edit(modified_text)
                        logging.info(f"Edited message in channel ID: {event.chat_id}")
                   except Exception as e:
                           logging.error(f"Error editing message in channel {event.chat_id}: {e}")
    
    copy_data = load_data()[3]
    if event.is_channel and str(event.chat_id) in copy_data:
        source_channel_id = event.chat_id
        destination_channel_id = copy_data[str(source_channel_id)]
        try:
           message = event.message  
           if message.media:
              await client.send_message(destination_channel_id, message=message.message, file=message.media)
              logging.info(f"Copied media message from {source_channel_id} to {destination_channel_id}")
           else:
              await client.send_message(destination_channel_id, message=message.message)
              logging.info(f"Copied message from {source_channel_id} to {destination_channel_id}")
        except Exception as e:
           logging.error(f"Error copying message from {source_channel_id} to {destination_channel_id}: {e}")


# Start the bot
with client:
    client.run_until_disconnected()
