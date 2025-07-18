import os
import json
import asyncio
import re
from telethon import TelegramClient, events, functions, types

# Environment variables - Make sure you set OWNER_ID as well
API_ID = int(os.getenv('28150346'))
API_HASH = os.getenv('426f0d0a1da02dea8fb71cb0bd3ab7e1')
BOT_TOKEN = os.getenv('7540024639:AAFHcQ5YuIOyNIZsKKgRrfw4nj5p-3s2WxU')
OWNER_ID = int(os.getenv('1251962299'))  # Add your user ID here as environment variable

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

@client.on(events.NewMessage(pattern='/help'))
async def help(event):
    """Provides help and contact information."""
    await event.respond('Yeh bot aapke channel ko manage karne ke liye hai.\n\n'
                        '/start - Welcome message aur bot ki jankari.\n'
                        '/help - Yeh help message.\n'
                        '/addchannel <channel_id> - Channel ko monitor karne ke liye add karein.\n'
                        '/removechannel <channel_id> - Monitored channel ko remove karein.\n'
                        '/showchannels - Added channels ki list dekhein.\n'
                        '/authorizeuser <user_id> - User ko link post karne ke liye authorize karein.\n'
                        '/unauthorizeuser <user_id> - Authorized user ko remove karein.\n'
                        '/showauthorizedusers - Authorized users ki list dekhein.\n'
                        '/postlink <text> <link> - Channel mein link post karein (sirf authorized users).\n'
                        '/testadmin <user_id> - Check if a user is admin in the channel (for debugging).\n' # Added testadmin to help
                        '\n'
                        'Koi bhi problem ho to @captain_stive par contact karein.')

@client.on(events.NewMessage(pattern=r'/addchannel (-?\d+)'))
async def add_channel(event):
    """Adds a channel ID to the list of monitored channels."""
    if not await is_authorized(event.sender_id):
        await event.respond("Sirf authorized users hi yeh command use kar sakte hain.")
        return

    try:
        channel_id = int(event.pattern_match.group(1))
        if channel_id not in CHANNEL_IDS:
            CHANNEL_IDS.append(channel_id)
            save_data(CHANNEL_IDS, text_links, authorized_user_ids)
            await event.respond(f'Channel ID {channel_id} add ho gaya! 👍')
        else:
            await event.respond(f'Channel ID {channel_id} pahle se hi add hai! ⚠️')
    except ValueError:
        await event.respond('Invalid channel ID. Please use a valid integer.')
    print(f"Current CHANNEL_IDS: {CHANNEL_IDS}")  # Debugging line: show current channel ids

@client.on(events.NewMessage(pattern=r'/removechannel (-?\d+)'))
async def remove_channel(event):
    """Removes a channel from the list of monitored channels."""
    if not await is_authorized(event.sender_id):
        await event.respond("Sirf authorized users hi yeh command use kar sakte hain.")
        return
    try:
        channel_id = int(event.pattern_match.group(1))
        if channel_id in CHANNEL_IDS:
            CHANNEL_IDS.remove(channel_id)
            save_data(CHANNEL_IDS, text_links, authorized_user_ids)
            await event.respond(f'Channel ID {channel_id} removed! 👍')
        else:
             await event.respond(f'Channel ID {channel_id} not found! ⚠️')
    except ValueError:
            await event.respond('Invalid channel ID. Please use a valid integer.')
    print(f"Current CHANNEL_IDS: {CHANNEL_IDS}") # Debugging line: show current channel ids

@client.on(events.NewMessage(pattern='/showchannels'))
async def show_channels(event):
    """Shows the list of added channels."""
    if not await is_authorized(event.sender_id):
        await event.respond("Sirf authorized users hi yeh command use kar sakte hain.")
        return
    if CHANNEL_IDS:
        channel_list = "\n".join([str(cid) for cid in CHANNEL_IDS])
        await event.respond(f'Current monitored channels:\n{channel_list}')
    else:
        await event.respond('No channels added yet.')
    print(f"Current CHANNEL_IDS: {CHANNEL_IDS}")  # Debugging line: show current channel ids


@client.on(events.NewMessage(pattern=r'/authorizeuser (\d+)'))
async def authorize_user(event):
    """Authorizes a user to use bot commands."""
    if not await is_authorized(event.sender_id):
        await event.respond("Sirf authorized users hi yeh command use kar sakte hain.")
        return
    try:
        user_id = int(event.pattern_match.group(1))
        if user_id not in authorized_user_ids:
            authorized_user_ids.append(user_id)
            save_data(CHANNEL_IDS, text_links, authorized_user_ids)
            await event.respond(f'User ID {user_id} authorized! 👍')
        else:
            await event.respond(f'User ID {user_id} pahle se hi authorized hai! ⚠️')
    except ValueError:
        await event.respond('Invalid User ID. Please use a valid integer.')
    print(f"Current authorized_user_ids: {authorized_user_ids}")

@client.on(events.NewMessage(pattern=r'/unauthorizeuser (\d+)'))
async def unauthorize_user(event):
    """Removes authorization from a user."""
    if not await is_authorized(event.sender_id):
        await event.respond("Sirf authorized users hi yeh command use kar sakte hain.")
        return
    try:
        user_id = int(event.pattern_match.group(1))
        if user_id != OWNER_ID: # Prevent removing owner from authorized users
            if user_id in authorized_user_ids:
                authorized_user_ids.remove(user_id)
                save_data(CHANNEL_IDS, text_links, authorized_user_ids)
                await event.respond(f'User ID {user_id} unauthorized! 👍')
            else:
                await event.respond(f'User ID {user_id} authorized nahi hai! ⚠️')
        else:
            await event.respond("Owner ko unauthorized nahi kiya ja sakta.")
    except ValueError:
        await event.respond('Invalid User ID. Please use a valid integer.')
    print(f"Current authorized_user_ids: {authorized_user_ids}")

@client.on(events.NewMessage(pattern='/showauthorizedusers'))
async def show_authorized_users(event):
    """Shows the list of authorized users."""
    if not await is_authorized(event.sender_id):
        await event.respond("Sirf authorized users hi yeh command use kar sakte hain.")
        return
    if authorized_user_ids:
        user_list = "\n".join([str(uid) for uid in authorized_user_ids])
        await event.respond(f'Current authorized users:\n{user_list}')
    else:
        await event.respond('No users authorized yet.')
    print(f"Current authorized_user_ids: {authorized_user_ids}")


@client.on(events.NewMessage(pattern=r'/postlink (.+) (https?://[^\s]+)'))
async def post_link_command(event):
    """Posts a link to all monitored channels - only for authorized users."""
    if not await is_authorized(event.sender_id):
        await event.respond("Sirf authorized users hi yeh command use kar sakte hain.")
        return

    text = event.pattern_match.group(1).strip()
    link = event.pattern_match.group(2)
    message_to_post = f"{text}\n{link}"

    for channel_id in CHANNEL_IDS:
        try:
            await client.send_message(channel_id, message_to_post)
            print(f"Link posted to channel ID: {channel_id}")
            await event.respond(f"Link posted to channel ID: {channel_id}") # Acknowledge to the user where it's posted. Consider better feedback.

        except Exception as e:
            await event.respond(f"Error posting to channel ID {channel_id}: {e}")
            print(f"Error posting to channel {channel_id}: {e}")

@client.on(events.NewMessage(pattern=r'/testadmin (\d+)'))
async def test_admin_command(event):
    """Test if a user is admin in the channel (for debugging)."""
    if not event.is_channel:
        await event.respond("Yeh command channel mein hi use karein.")
        return
    try:
        user_id_to_test = int(event.pattern_match.group(1))
        channel_id_to_test = event.chat_id # Assuming you run this command in the channel
        is_admin = await is_admin_in_channel(user_id_to_test, channel_id_to_test)
        await event.respond(f"User {user_id_to_test} is admin in this channel: {is_admin}")
    except ValueError:
        await event.respond("Invalid User ID. Please use a valid integer.")


@client.on(events.NewMessage())
async def delete_admin_links(event):
    """Deletes links posted by other admins in monitored channels."""
    print("New message event triggered.") # Debugging print
    if not event.is_channel:
        print("Not a channel message, ignoring.") # Debugging print
        return
    if event.chat_id not in CHANNEL_IDS:
        print(f"Channel ID {event.chat_id} ({event.chat_id}) not in monitored channels, ignoring.") # Debugging print
        return

    if event.message.entities:
        print("Message entities found.") # Debugging print
        for entity in event.message.entities:
            if isinstance(entity, (types.MessageEntityUrl, types.MessageEntityTextUrl)):
                print("URL entity detected.") # Debugging print
                sender_id = event.sender_id
                bot_id = client.session.user_id
                print(f"Sender ID: {sender_id}, Bot ID: {bot_id}") # Debugging print

                if sender_id != bot_id: # Ignore messages sent by the bot itself
                    print("Sender is not the bot.") # Debugging print
                    is_sender_admin = await is_admin_in_channel(sender_id, event.chat_id)
                    print(f"Is sender admin: {is_sender_admin}") # Debugging print
                    if is_sender_admin:
                        print(f"Link detected from admin {sender_id} in channel {event.chat_id}. Deleting in 5 seconds...") # Debugging print
                        await asyncio.sleep(5) # Wait for 5 seconds
                        try:
                            await event.delete()
                            print(f"Link message deleted from admin {sender_id} in channel {event.chat_id}.") # Debugging print
                        except Exception as e:
                            print(f"Error deleting message: {e}") # Debugging print
                        return # Delete only the first link message


# Start the bot
with client:
    client.run_until_disconnected()
