import os
import json
from telethon import TelegramClient, events, types
from telethon.errors import ChatAdminRequiredError
from datetime import datetime, timedelta
import logging
import re

# Environment variables
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
NOTIFICATION_CHANNEL_ID = int(os.getenv('NOTIFICATION_CHANNEL_ID'))

# File to store data
DATA_FILE = 'bot_data.json'

# Load data from file or initialize if not exists
def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            return (
                data.get('channel_ids', []),
                data.get('text_links', {}),
                data.get('user_data', {}),
                data.get('copy_data', {})
            )
    except (FileNotFoundError, json.JSONDecodeError):
        return [], {}, {}, {}

# Save data to file
def save_data(channel_ids, text_links, user_data, copy_data):
    data = {
        'channel_ids': channel_ids,
        'text_links': text_links,
        'user_data': user_data,
        'copy_data': copy_data
    }
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Initialize the bot with data from storage
CHANNEL_IDS, text_links, user_data, copy_data = load_data()

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
    if user_id in user_data:
        start_date = datetime.fromisoformat(user_data[user_id]['start_date'])
        trial_end_date = start_date + timedelta(days=3)
        return datetime.now() <= trial_end_date, False
    return True, True

def is_user_active(user_id):
    if user_id in user_data:
        if user_data[user_id].get('is_paid', False):
            start_date = datetime.fromisoformat(user_data[user_id]['start_date'])
            end_date = start_date + timedelta(days=30)
            return datetime.now() <= end_date
        else:
            return is_trial_active(user_id)[0]
    else:
        return is_trial_active(user_id)[0]

def check_user_status(user_id):
    if user_id in user_data:
        if user_data[user_id].get('is_blocked', False):
            return False
        else:
            return is_user_active(user_id)
    else:
        return is_trial_active(user_id)[0]

@client.on(events.NewMessage(pattern='/addcopy'))
async def add_copy(event):
    """Adds copying between two channels and starts copying old messages."""
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

        # Add the copy setup
        if str(source_channel_id) not in copy_data:
            copy_data[str(source_channel_id)] = destination_channel_id
            save_data(CHANNEL_IDS, text_links, user_data, copy_data)
            await event.respond(f'Messages from channel {source_channel_id} will now be copied to {destination_channel_id}. Old messages will also be copied.')
            await send_notification(f"Copying set by user {event.sender_id}:\nSource: {source_channel_id}\nDestination: {destination_channel_id}")

            # Copy old messages
            await copy_old_messages(source_channel_id, destination_channel_id)
        else:
            await event.respond(f'Copying from {source_channel_id} already set. ⚠️')
    except ValueError:
        await event.respond('Invalid channel ID. Please use a valid integer.')
    except ChatAdminRequiredError:
        await event.respond('Bot needs to be an admin in the source channel to fetch old messages.')
    logging.info(f"Current copy_data: {copy_data}")

async def copy_old_messages(source_channel_id, destination_channel_id):
    """Fetch and copy old messages from the source to the destination channel."""
    try:
        async for message in client.iter_messages(source_channel_id, reverse=True):
            if message.media:
                await client.send_message(destination_channel_id, message=message.message, file=message.media)
            else:
                await client.send_message(destination_channel_id, message=message.message)
            logging.info(f"Copied old message from {source_channel_id} to {destination_channel_id}")
    except Exception as e:
        logging.error(f"Error copying old messages from {source_channel_id} to {destination_channel_id}: {e}")

@client.on(events.NewMessage())
async def copy_new_messages(event):
    """Copies new messages based on the set copy data."""
    if event.is_channel and str(event.chat_id) in copy_data:
        source_channel_id = event.chat_id
        destination_channel_id = copy_data[str(source_channel_id)]
        try:
            message = event.message
            if message.media:
                await client.send_message(destination_channel_id, message=message.message, file=message.media)
            else:
                await client.send_message(destination_channel_id, message=message.message)
            logging.info(f"Copied new message from {source_channel_id} to {destination_channel_id}")
        except Exception as e:
            logging.error(f"Error copying new message from {source_channel_id} to {destination_channel_id}: {e}")

# Start the bot
with client:
    client.run_until_disconnected()
