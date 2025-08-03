import os
import json
from telethon import TelegramClient, events
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
                 data.get('total_users', 0),
                data.get('active_channel_id', None)
            )
    except (FileNotFoundError, json.JSONDecodeError):
        return [], {}, {}, 0, None

# Save data to file
def save_data(channel_ids, text_links, user_data,total_users,active_channel_id):
    data = {
        'channel_ids': channel_ids,
        'text_links': text_links,
        'user_data': user_data,
        'total_users': total_users,
        'active_channel_id': active_channel_id
    }
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Initialize the bot with data from storage
CHANNEL_IDS, text_links, user_data, total_users, active_channel_id = load_data()

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

    return True, True # New user always gets the free trail
    
def is_user_active(user_id):
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
    if user_id in user_data:
        if user_data[user_id].get('is_blocked',False):
            return False
        else:
            return is_user_active(user_id)
    else:
        return is_trial_active(user_id)


@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Sends a welcome message when the bot starts."""
    global total_users  # Use the global keyword to modify total_users
    user_id = event.sender_id
    logging.info(f"User ID {user_id} used /start command.")

    if not check_user_status(user_id):
       await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
       return
    
    is_new_user = user_id not in user_data
    if is_new_user:
       user_data[user_id] = {
        'start_date': datetime.now().isoformat(),
        'is_paid':False,
        'is_blocked':False
        }
       total_users += 1  # Increment total_users for each new user
       save_data(CHANNEL_IDS, text_links, user_data,total_users,active_channel_id)
       user = await client.get_entity(user_id)
       username = user.username if user.username else "N/A"
       await send_notification(f"New user started the bot:\nUser ID: {user_id}\nUsername: @{username}")

    welcome_message = 'Namaste! 🙏 Bot mein aapka swagat hai! \n\n' \
                      'Ye bot aapke messages mein automatically links add kar dega.\n\n' \
                      'Agar aapko koi problem ho ya help chahiye, to /help command use karein.\n\n' \
                      'Bot ke sabhi commands dekhne ke liye /allcommands type karein.\n\n'
    await event.respond(welcome_message)


@client.on(events.NewMessage(pattern='/allcommands'))
async def all_commands(event):
    """Sends a list of all available commands."""
    if not check_user_status(event.sender_id):
        await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
        return
    commands_list = (
        '/start - Bot ko start karne ke liye.\n'
        '/help - Bot ke support ke liye.\n'
        '/addchannel - Channel ID add karein (jaise: /addchannel -100123456789).\n'
        '/addlink - Text aur link add karein (jaise: /addlink text link).\n'
        '/showchannels - Added channels dekhe.\n'
        '/showlinks - Added links dekhe.\n'
        '/removechannel - Channel remove karein (jaise: /removechannel -100123456789).\n'
        '/removelink - Link remove karein (jaise: /removelink text).\n'
        '/totalusers - Bot ko use krne wale users dekhe.\n'
        '/broadcast - Sab users ko msg bheje.\n'
        '/selectchannel - Channel select karein (jaise: /selectchannel -100123456789).\n'
        '/deselectchannel - Channel deselect karein.\n'
    )
    await event.respond(f'Bot commands:\n\n{commands_list}')

@client.on(events.NewMessage(pattern='/help'))
async def help(event):
    """Provides help and contact information."""
    if not check_user_status(event.sender_id):
       await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
       return
    await event.respond('Aapko koi bhi problem ho, to mujhe yahaan contact karein: @captain_stive')

@client.on(events.NewMessage(pattern=r'/addchannel'))
async def add_channel(event):
    """Adds a channel ID to the list of monitored channels with format validation."""
    if not check_user_status(event.sender_id):
        await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
        return

    full_command = event.text.strip()
    match = re.match(r'/addchannel (-?\d+)', full_command)
    if not match:
        await event.respond('Invalid command format. Use: /addchannel -100123456789')
        return

    try:
        channel_id = int(match.group(1))
        if channel_id not in CHANNEL_IDS:
            CHANNEL_IDS.append(channel_id)
            save_data(CHANNEL_IDS, text_links,user_data,total_users,active_channel_id)
            await event.respond(f'Channel ID {channel_id} add ho gaya! 👍')
            await send_notification(f"Channel added by user {event.sender_id}:\nChannel ID: {channel_id}")
        else:
            await event.respond(f'Channel ID {channel_id} pahle se hi add hai! ⚠️')
    except ValueError:
        await event.respond('Invalid channel ID. Please use a valid integer.')
    logging.info(f"Current CHANNEL_IDS: {CHANNEL_IDS}")

@client.on(events.NewMessage(pattern=r'/addlink'))
async def add_link(event):
    """Adds a text and link pair to the dictionary with format validation."""
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
    text_links[text] = link
    save_data(CHANNEL_IDS, text_links,user_data,total_users,active_channel_id)
    await event.respond(f'Text "{text}" aur link "{link}" add ho gaya! 👍')
    await send_notification(f"Link added by user {event.sender_id}:\nText: {text}\nLink: {link}")
    logging.info(f"Current text_links: {text_links}")

@client.on(events.NewMessage(pattern='/showchannels'))
async def show_channels(event):
    """Shows the list of added channels."""
    if not check_user_status(event.sender_id):
        await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
        return
    if CHANNEL_IDS:
        channel_list = "\n".join([str(cid) for cid in CHANNEL_IDS])
        await event.respond(f'Current monitored channels:\n{channel_list}')
    else:
        await event.respond('No channels added yet.')
    logging.info(f"Current CHANNEL_IDS: {CHANNEL_IDS}")

@client.on(events.NewMessage(pattern='/showlinks'))
async def show_links(event):
    """Shows the list of added text and links."""
    if not check_user_status(event.sender_id):
         await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
         return
    if text_links:
        link_list = "\n".join([f'{text}: {link}' for text, link in text_links.items()])
        await event.respond(f'Current links:\n{link_list}')
    else:
        await event.respond('No links added yet.')
    logging.info(f"Current text_links: {text_links}")

@client.on(events.NewMessage(pattern=r'/removechannel'))
async def remove_channel(event):
    """Removes a channel from the list of monitored channels with format validation."""
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
        if channel_id in CHANNEL_IDS:
            CHANNEL_IDS.remove(channel_id)
            save_data(CHANNEL_IDS, text_links,user_data,total_users,active_channel_id)
            await event.respond(f'Channel ID {channel_id} removed! 👍')
        else:
             await event.respond(f'Channel ID {channel_id} not found! ⚠️')
    except ValueError:
            await event.respond('Invalid channel ID. Please use a valid integer.')
    logging.info(f"Current CHANNEL_IDS: {CHANNEL_IDS}")

@client.on(events.NewMessage(pattern=r'/removelink'))
async def remove_link(event):
    """Removes a text-link pair from the dictionary with format validation."""
    if not check_user_status(event.sender_id):
        await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
        return

    full_command = event.text.strip()
    match = re.match(r'/removelink (.+)', full_command)
    if not match:
        await event.respond('Invalid command format. Use: /removelink text (eg: /removelink mytext)')
        return
        
    text = match.group(1).strip()
    if text in text_links:
        del text_links[text]
        save_data(CHANNEL_IDS, text_links,user_data,total_users,active_channel_id)
        await event.respond(f'Link with text "{text}" removed! 👍')
    else:
         await event.respond(f'Link with text "{text}" not found! ⚠️')
    logging.info(f"Current text_links: {text_links}")

@client.on(events.NewMessage(pattern='/totalusers'))
async def total_users_command(event):
    """Displays the total number of users who have used the bot. Only for admin."""
    if event.sender_id == ADMIN_ID:
        await event.respond(f"Total users who have started the bot: {total_users}")
    else:
         await event.respond("You are not authorized to use this command.")

@client.on(events.NewMessage(pattern='/broadcast'))
async def broadcast_message(event):
    """Sends a message to all users who have started the bot. Only for admin."""
    if event.sender_id != ADMIN_ID:
        await event.respond("You are not authorized to use this command.")
        return
    
    if event.sender_id != event.chat_id:  # Check if the command is sent in private
        await event.respond("This command should be used in a private chat with the bot.")
        return
    
    full_command = event.text.strip()
    match = re.match(r'/broadcast (.+)', full_command, re.DOTALL)
    if not match:
        await event.respond('Invalid command format. Use: /broadcast <message>')
        return

    message_to_send = match.group(1).strip()
    sent_count = 0
    
    for user_id in user_data:
       try:
          await client.send_message(user_id, message_to_send)
          sent_count += 1
          logging.info(f"Broadcast msg send to: {user_id}")
       except Exception as e:
           logging.error(f"Error sending broadcast message to {user_id}: {e}")

    await event.respond(f"Broadcast message sent to {sent_count} users.")

@client.on(events.NewMessage(pattern=r'/adminactivate'))
async def activate_user(event):
    """Activates a user for 30 days after payment. Only admin can use this command."""
    if event.sender_id != ADMIN_ID:
        await event.respond("You are not authorized to use this command.")
        return
    
    if event.sender_id != event.chat_id:  # Check if the command is sent in private
        await event.respond("This command should be used in a private chat with the bot.")
        return
    
    full_command = event.text.strip()
    match = re.match(r'/adminactivate (-?\d+)', full_command)
    if not match:
        await event.respond('Invalid command format. Use: /adminactivate <user_id>')
        return
        
    try:
        user_id_to_activate = int(match.group(1))
        if user_id_to_activate in user_data:
            user_data[user_id_to_activate]['start_date'] = datetime.now().isoformat()
            user_data[user_id_to_activate]['is_paid'] = True
            user_data[user_id_to_activate]['is_blocked'] = False
            save_data(CHANNEL_IDS, text_links, user_data,total_users,active_channel_id)
            await event.respond(f'User ID {user_id_to_activate} activated for 30 days! ✅')
            # Send a congratulatory message to the user
            await client.send_message(user_id_to_activate, "Congratulations! Your account has been activated for 30 days. Enjoy using the bot!")
        else:
             await event.respond(f'User ID {user_id_to_activate} not found! ⚠️')
    except ValueError:
       await event.respond('Invalid user ID. Please use a valid integer.')

@client.on(events.NewMessage(pattern=r'/adminblock'))
async def block_user(event):
    """Blocks a user from using the bot. Only admin can use this command."""
    if event.sender_id != ADMIN_ID:
        await event.respond("You are not authorized to use this command.")
        return
    
    if event.sender_id != event.chat_id:  # Check if the command is sent in private
        await event.respond("This command should be used in a private chat with the bot.")
        return
    
    full_command = event.text.strip()
    match = re.match(r'/adminblock (-?\d+)', full_command)
    if not match:
        await event.respond('Invalid command format. Use: /adminblock <user_id>')
        return
        
    try:
        user_id_to_block = int(match.group(1))
        if user_id_to_block in user_data:
            user_data[user_id_to_block]['is_blocked'] = True
            save_data(CHANNEL_IDS, text_links, user_data,total_users,active_channel_id)
            await event.respond(f'User ID {user_id_to_block} blocked! 🚫')
        else:
             await event.respond(f'User ID {user_id_to_block} not found! ⚠️')
    except ValueError:
       await event.respond('Invalid user ID. Please use a valid integer.')
    
@client.on(events.NewMessage(pattern=r'/adminunblock'))
async def unblock_user(event):
    """Unblocks a user from using the bot. Only admin can use this command."""
    if event.sender_id != ADMIN_ID:
        await event.respond("You are not authorized to use this command.")
        return
    
    if event.sender_id != event.chat_id:  # Check if the command is sent in private
        await event.respond("This command should be used in a private chat with the bot.")
        return
    
    full_command = event.text.strip()
    match = re.match(r'/adminunblock (-?\d+)', full_command)
    if not match:
        await event.respond('Invalid command format. Use: /adminunblock <user_id>')
        return
    
    try:
        user_id_to_unblock = int(match.group(1))
        if user_id_to_unblock in user_data:
            user_data[user_id_to_unblock]['is_blocked'] = False
            save_data(CHANNEL_IDS, text_links, user_data,total_users,active_channel_id)
            await event.respond(f'User ID {user_id_to_unblock} unblocked! ✅')
        else:
             await event.respond(f'User ID {user_id_to_unblock} not found! ⚠️')
    except ValueError:
       await event.respond('Invalid user ID. Please use a valid integer.')
    
@client.on(events.ChatAction)
async def handle_chat_actions(event):
    """Handles chat actions, specifically bot added to channel."""
    if event.user_added and event.who == await client.get_me():
       try:
            chat = await client.get_entity(event.chat_id)
            if chat.username:
               await send_notification(f"Bot added to channel: @{chat.username}")
            else:
               await send_notification(f"Bot added to channel: {chat.title}")
       except Exception as e:
            logging.error(f"Error getting chat username: {e}")
    
@client.on(events.NewMessage(pattern=r'/selectchannel'))
async def select_channel(event):
    """Selects a channel for applying link replacements with format validation."""
    global active_channel_id
    if not check_user_status(event.sender_id):
         await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
         return

    full_command = event.text.strip()
    match = re.match(r'/selectchannel (-?\d+)', full_command)
    if not match:
        await event.respond('Invalid command format. Use: /selectchannel -100123456789')
        return

    try:
        channel_id = int(match.group(1))
        if channel_id in CHANNEL_IDS:
            active_channel_id = channel_id
            save_data(CHANNEL_IDS, text_links, user_data, total_users,active_channel_id)
            await event.respond(f'Channel ID {channel_id} selected for link replacement! ✅')
            await send_notification(f"Active channel selected by user {event.sender_id}: Channel ID: {channel_id}")
        else:
            await event.respond(f'Channel ID {channel_id} not found in the added channels! ⚠️')

    except ValueError:
            await event.respond('Invalid channel ID. Please use a valid integer.')
    logging.info(f"Active Channel ID: {active_channel_id}")

@client.on(events.NewMessage(pattern=r'/deselectchannel'))
async def deselect_channel(event):
    """Deselects the active channel."""
    global active_channel_id
    if not check_user_status(event.sender_id):
         await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
         return
    if active_channel_id is not None:
        active_channel_id = None
        save_data(CHANNEL_IDS, text_links, user_data, total_users,active_channel_id)
        await event.respond('Active channel deselected. Link replacements will not be applied until a channel is selected. ✅')
        await send_notification(f"Active channel deselected by user {event.sender_id}")
    else:
        await event.respond('No channel is currently selected as active channel. ⚠️')
    logging.info(f"Active Channel ID: {active_channel_id}")

@client.on(events.NewMessage())
async def add_links(event):
    user_id = event.sender_id
    if not check_user_status(user_id):
        if event.is_private:
            await event.respond(f'Aapki free trial khatam ho gyi hai, please contact kare @captain_stive')
        return

    if event.is_channel and event.chat_id == active_channel_id:
        logging.info(f"Message received from channel ID: {event.chat_id}")
        message_text = event.message.message
        for text, link in text_links.items():
            if message_text.strip() == text:
                new_message_text = f"{text}\n{link}"
                try:
                    await event.edit(new_message_text)
                    logging.info(f"Edited message in channel ID: {event.chat_id}")
                except Exception as e:
                    logging.error(f"Error editing message in channel {event.chat_id}: {e}")
                break

# Start the bot
with client:
    client.run_until_disconnected()
