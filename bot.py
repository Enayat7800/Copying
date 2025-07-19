import os
import json
import asyncio
import re
from telethon import TelegramClient, events, functions, types

# Direct values (Environment variables hata diye gaye hain)
API_ID = 28150346
API_HASH = '426f0d0a1da02dea8fb71cb0bd3ab7e1'
BOT_TOKEN = '7540024639:AAFHcQ5YuIOyNIZsKKgRrfw4nj5p-3s2WxU'
OWNER_ID = 1251962299  # Owner ID directly set

# File to store data
DATA_FILE = 'bot_data.json'

# Load data from file or initialize if not exists
def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            return data.get('channel_ids', []), data.get('text_links', {}), data.get('authorized_user_ids', [OWNER_ID]) # Initialize authorized users with owner
    except (FileNotFoundError, json.JSONDecodeError):
        return [], {}, [OWNER_ID] # Initialize authorized users with owner

# Save data to file
def save_data(channel_ids, text_links, authorized_user_ids):
    data = {'channel_ids': channel_ids, 'text_links': text_links, 'authorized_user_ids': authorized_user_ids}
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)


# Initialize the bot with data from storage
CHANNEL_IDS, text_links, authorized_user_ids = load_data()


# Initialize the client
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

async def is_authorized(user_id):
    return user_id in authorized_user_ids

async def is_admin_in_channel(user_id, channel_id):
    try:
        participant = await client.get_permissions(channel_id, user_id)
        return participant.is_admin or participant.is_creator
    except Exception as e:
        print(f"Error checking admin status: {e}")
        return False


@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Sends a welcome message when the bot starts."""
    await event.respond('Namaste! 🙏  Bot mein aapka swagat hai! \n\n'
                        'Ye bot aapke channel ko manage karne mein madad karega.\n\n'
                        'Sirf authorized users hi link post kar sakte hain command ke through.\n\n'
                        'Agar koi aur admin link post karta hai to bot use 5 second mein delete kar dega.\n\n'
                        'Agar aapko koi problem ho ya help chahiye, to /help command use karein.\n\n'
                        'Naye channel add karne ke liye, /addchannel command use karein (jaise: /addchannel -100123456789).\n\n'
                        'Authorized user add karne ke liye /authorizeuser command use karein (jaise: /authorizeuser 123456789).\n\n'
                        'Authorized user remove karne ke liye /unauthorizeuser command use karein (jaise: /unauthorizeuser 123456789).\n\n'
                        'Channel remove karne ke liye /removechannel command use karein (jaise: /removechannel -100123456789).\n\n'
                         'Agar aapko added channel dekhna hai to /showchannels command use karein.\n\n'
                         'Authorized users dekhne ke liye /showauthorizedusers command use karein.\n\n'
                         'Link post karne ke liye /postlink command use karein (jaise: /postlink Message_text https://link.com).\n\n'
                         'Bot owner: Aap hi hain (user ID: {})'.format(OWNER_ID))

# (baaki code aise hi continue hota hai jaise aapne diya hai...)
