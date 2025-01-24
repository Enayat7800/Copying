from telethon import TelegramClient, events, Button
import asyncio
import os
import re

# Environment Variables
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Client Setup
bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Channel List Storage
channel_ids = set()

# /start Command
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.is_private:
        await event.reply(
            "Hi! 👋 Main ek movie search bot hoon.\n\n"
            "Bas movie ya series ka naam bhejiye, aur main usse dhoondh kar bhej dunga!\n\n"
            "Commands:\n"
            "/addchannel <channel_id> - Add a channel for search\n"
            "/removechannel <channel_id> - Remove a channel from search\n"
            "/listchannels - List all added channels\n"
            "Note: Yeh bot un sabhi channels mein search karega jisme yeh admin hai, or vo channels jo manually add kiye gaye hai."
        )

# Command to Add Channels
@bot.on(events.NewMessage(pattern='/addchannel'))
async def add_channel(event):
    if event.is_private:
        try:
            channel_id = int(event.raw_text.split(' ')[1])
            if channel_id not in channel_ids:
                channel_ids.add(channel_id)
                await event.reply(f'Channel ID {channel_id} added successfully!')
            else:
                await event.reply('This channel is already added.')
        except (IndexError, ValueError):
            await event.reply('Please provide a valid Channel ID. Example: /addchannel -100123456789')
            
# Command to Remove Channels
@bot.on(events.NewMessage(pattern='/removechannel'))
async def remove_channel(event):
    if event.is_private:
        try:
            channel_id = int(event.raw_text.split(' ')[1])
            if channel_id in channel_ids:
                channel_ids.remove(channel_id)
                await event.reply(f'Channel ID {channel_id} removed successfully!')
            else:
                await event.reply('This channel is not in the list.')
        except (IndexError, ValueError):
            await event.reply('Please provide a valid Channel ID to remove. Example: /removechannel -100123456789')

# Command to list added channels
@bot.on(events.NewMessage(pattern='/listchannels'))
async def list_channels(event):
    if event.is_private:
        if channel_ids:
            await event.reply(f'Currently added channels: {", ".join(map(str,channel_ids))}')
        else:
            await event.reply('No channels are added currently')

# Handle File/Video Name Directly
@bot.on(events.NewMessage)
async def handle_query(event):
    if event.is_private:
        query = event.raw_text.lower()
        print(f"Searching for: {query}")

        found_results = {}
         # Get the list of channels where the bot is an admin
        admin_channels = []
        async for dialog in bot.iter_dialogs():
            if dialog.is_channel and dialog.entity.admin_rights is not None:
              admin_channels.append(dialog.entity.id)


         # Search in admin channels and manually added channels
        all_channels = admin_channels + list(channel_ids)
        print(f"Searching in channels: {all_channels}")
        
        # search in all available channels
        for channel_id in all_channels:
            async for message in bot.iter_messages(channel_id): # remove the search term and send all the messages for filtering
                 if message.file:  # Check if the message contains a file or video
                     text_to_match = message.file.name if message.file and message.file.name else message.text if message.text else ""
                     if text_to_match:
                        # Create regex pattern with word boundaries to match whole words
                        pattern = re.compile(r'\b' + re.escape(query) + r'\b', re.IGNORECASE)
                        if pattern.search(text_to_match):
                            found_results[message.id] = {"channel_id":channel_id, "message":message}


        if found_results:
           
           if len(found_results) == 1 :
                message_id = list(found_results.keys())[0]
                message_data = found_results[message_id]
                
                await event.reply(
                        f"Here is the movie/series you requested (will be deleted in 5 minutes):",
                        file=message_data["message"].file
                    )
                
                # Schedule message deletion after 5 minutes
                await asyncio.sleep(300)  # 5 minutes
                await bot.delete_messages(event.chat_id, event.message.id)
                
           else:
                buttons = []
                for message_id, message_data in found_results.items():
                    channel_name = (await bot.get_entity(message_data["channel_id"])).title
                    
                    buttons.append(
                      Button.inline(f"{channel_name} - {message_data['message'].file.name if message_data['message'].file else 'No Name'} ", data=f"select_movie_{message_id}")
                    )
                
                await event.reply("Multiple results found, please select an option:", buttons= [buttons[i:i+2] for i in range(0, len(buttons), 2)] )
           
        else:
             await event.reply('No movies or series found matching your query.')

@bot.on(events.CallbackQuery(data=lambda data: data.startswith("select_movie_")))
async def handle_movie_selection(event):
    selected_message_id = int(event.data.split("_")[-1])
    
    
    admin_channels = []
    async for dialog in bot.iter_dialogs():
        if dialog.is_channel and dialog.entity.admin_rights is not None:
          admin_channels.append(dialog.entity.id)

    all_channels = admin_channels + list(channel_ids)
    
    selected_message = None
    for channel_id in all_channels:
       async for message in bot.iter_messages(channel_id, ids=selected_message_id):
           selected_message = message
           break
       if selected_message:
            break
           
    if selected_message:
        await event.edit(
                    f"Here is the movie/series you requested (will be deleted in 5 minutes):",
                    file=selected_message.file, buttons = None
                )
        # Schedule message deletion after 5 minutes
        await asyncio.sleep(300)  # 5 minutes
        await bot.delete_messages(event.chat_id, event.message.id)
    else :
        await event.edit("Error movie not found", buttons = None)

# Start the bot
print("Bot is running...")
bot.run_until_disconnected()
