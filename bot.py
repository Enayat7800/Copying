from telethon import TelegramClient, events, Button
import asyncio
import os

# Environment Variables
API_ID = int(os.getenv('API_ID'))  # Railway environment me integer conversion zaroori hai
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Client Setup
bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)


# /start Command
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.is_private:
        await event.reply(
            "Hi! 👋 Main ek movie search bot hoon.\n\n"
            "Bas movie ya series ka naam bhejiye, aur main usse dhoondh kar bhej dunga!\n\n"
            "Note: Yeh bot un sabhi channels mein search karega jisme yeh admin hai."
        )

# Handle File/Video Name Directly
@bot.on(events.NewMessage)
async def handle_query(event):
    if event.is_private:
        query = event.raw_text.lower()
        found_results = {}
        
        # Get the list of channels where the bot is an admin
        dialogs = await bot.get_dialogs()
        admin_channels = [dialog for dialog in dialogs if dialog.is_channel and dialog.entity.admin_rights is not None]

        # Search in all admin channels
        for channel in admin_channels:
           
            async for message in bot.iter_messages(channel.id, search=query):
                if message.file:  # Check if the message contains a file or video
                   found_results[message.id] = {"channel_id":channel.id, "message":message}
        
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
             await event.reply('No movies or series found matching your query in the channels where I am admin.')

@bot.on(events.CallbackQuery(data=lambda data: data.startswith("select_movie_")))
async def handle_movie_selection(event):
    selected_message_id = int(event.data.split("_")[-1])
    
    dialogs = await bot.get_dialogs()
    admin_channels = [dialog for dialog in dialogs if dialog.is_channel and dialog.entity.admin_rights is not None]
    
    selected_message = None
    for channel in admin_channels:
       async for message in bot.iter_messages(channel.id, ids=selected_message_id):
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
