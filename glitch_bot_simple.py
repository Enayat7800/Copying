import os
import json
import asyncio
import re
from telethon import TelegramClient, events, functions, types
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# HTTP Server for keep-alive (Glitch requirement)
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<h1>Bot is Running!</h1><p>Glitch Hosting Active</p>')
    def log_message(self, format, *args): pass

def start_health_server():
    try:
        port = int(os.getenv('PORT', 8080))
        server = HTTPServer(('0.0.0.0', port), HealthHandler)
        print(f"Health server started on port {port}")
        server.serve_forever()
    except Exception as e:
        print(f"Health server error: {e}")

# Start HTTP server in background
health_thread = threading.Thread(target=start_health_server, daemon=True)
health_thread.start()

# Bot credentials from environment
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID'))

print(f"Bot starting with Owner ID: {OWNER_ID}")

# Data storage
DATA_FILE = 'bot_data.json'

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            return data.get('channel_ids', []), data.get('authorized_user_ids', [OWNER_ID])
    except:
        return [], [OWNER_ID]

def save_data(channel_ids, authorized_user_ids):
    data = {'channel_ids': channel_ids, 'authorized_user_ids': authorized_user_ids}
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

CHANNEL_IDS, authorized_user_ids = load_data()

# Initialize Telegram client
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

async def is_authorized(user_id):
    return user_id in authorized_user_ids

async def is_admin_in_channel(user_id, channel_id):
    try:
        participant = await client.get_permissions(channel_id, user_id)
        return participant.is_admin or participant.is_creator
    except:
        return False

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond(f'🤖 Bot Active!\n\nOwner: {OWNER_ID}\nHosted on: Glitch\n\nCommands:\n/addchannel <id>\n/postlink <text> <url>\n/help')

@client.on(events.NewMessage(pattern='/help'))
async def help(event):
    await event.respond('Commands:\n/addchannel <channel_id>\n/removechannel <channel_id>\n/showchannels\n/authorizeuser <user_id>\n/postlink <text> <link>')

@client.on(events.NewMessage(pattern=r'/addchannel (-?\d+)'))
async def add_channel(event):
    if not await is_authorized(event.sender_id):
        await event.respond("Only authorized users can use this.")
        return
    
    channel_id = int(event.pattern_match.group(1))
    if channel_id not in CHANNEL_IDS:
        CHANNEL_IDS.append(channel_id)
        save_data(CHANNEL_IDS, authorized_user_ids)
        await event.respond(f'Channel {channel_id} added!')
    else:
        await event.respond('Channel already exists!')

@client.on(events.NewMessage(pattern='/showchannels'))
async def show_channels(event):
    if not await is_authorized(event.sender_id):
        return
    if CHANNEL_IDS:
        await event.respond(f'Channels:\n' + '\n'.join(map(str, CHANNEL_IDS)))
    else:
        await event.respond('No channels added.')

@client.on(events.NewMessage(pattern=r'/authorizeuser (\d+)'))
async def authorize_user(event):
    if not await is_authorized(event.sender_id):
        return
    user_id = int(event.pattern_match.group(1))
    if user_id not in authorized_user_ids:
        authorized_user_ids.append(user_id)
        save_data(CHANNEL_IDS, authorized_user_ids)
        await event.respond(f'User {user_id} authorized!')

@client.on(events.NewMessage(pattern=r'/postlink (.+) (https?://[^\s]+)'))
async def post_link(event):
    if not await is_authorized(event.sender_id):
        return
    
    text = event.pattern_match.group(1).strip()
    link = event.pattern_match.group(2)
    message = f"{text}\n{link}"
    
    for channel_id in CHANNEL_IDS:
        try:
            await client.send_message(channel_id, message)
            await event.respond(f"Posted to {channel_id}")
        except Exception as e:
            await event.respond(f"Error: {e}")

@client.on(events.NewMessage())
async def delete_admin_links(event):
    if not event.is_channel or event.chat_id not in CHANNEL_IDS:
        return
    
    if event.message.entities:
        for entity in event.message.entities:
            if isinstance(entity, (types.MessageEntityUrl, types.MessageEntityTextUrl)):
                sender_id = event.sender_id
                if sender_id != client.session.user_id:
                    if await is_admin_in_channel(sender_id, event.chat_id):
                        await asyncio.sleep(5)
                        try:
                            await event.delete()
                            print(f"Link deleted from admin {sender_id}")
                        except Exception as e:
                            print(f"Delete error: {e}")
                        return

print("Starting Telegram Bot...")
print("Health server running...")

# Start the bot
with client:
    client.run_until_disconnected()