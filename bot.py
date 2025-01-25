import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    InlineQueryHandler
)
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, Session
from fuzzywuzzy import process

# Configuration
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
DATABASE_URL = os.getenv("DATABASE_URL")

# Database Setup
Base = declarative_base()
engine = create_engine(DATABASE_URL)

class MediaFile(Base):
    __tablename__ = 'media_files'
    id = Column(Integer, primary_key=True)
    file_id = Column(String(255), unique=True)
    title = Column(String(255))
    quality = Column(String(50))
    type = Column(String(10))  # Movie/Series
    season = Column(Integer)
    episode = Column(Integer)
    caption = Column(Text)

Base.metadata.create_all(engine)

# Telegram Bot Setup
application = ApplicationBuilder().token(TOKEN).build()

# Custom Parser for Your Channel Format
def parse_caption(caption):
    patterns = [
        (r'(.*?)\s*(S\d+E\d+)', 'series'),  # Series pattern: Title S01E02
        (r'(.*?)\s*(\d{4})', 'movie')      # Movie pattern: Title (2023)
    ]
    
    for pattern, media_type in patterns:
        match = re.search(pattern, caption)
        if match:
            title = match.group(1).strip()
            details = match.group(2)
            
            if media_type == 'series':
                season_ep = re.findall(r'\d+', details)
                return {
                    'title': title,
                    'type': 'series',
                    'season': int(season_ep[0]),
                    'episode': int(season_ep[1]) if len(season_ep)>1 else None
                }
            else:
                return {
                    'title': f"{title} ({details})",
                    'type': 'movie'
                }
    return {'title': caption, 'type': 'unknown'}

# Search with Series Support
async def search_media(query):
    with Session(engine) as session:
        all_titles = [m.title for m in session.query(MediaFile).all()]
    
    matches = process.extractBests(query, all_titles, score_cutoff=75)
    
    with Session(engine) as session:
        return session.query(MediaFile).filter(
            MediaFile.title.in_([m[0] for m in matches])
        ).all()

# Bot Commands
async def start(update: Update, _):
    await update.message.reply_text(
        "🎥 Movie/Series Bot\n\n"
        "Search using:\n"
        "/find <name>\n"
        "Example: /find Oppenheimer"
    )

async def find(update: Update, context):
    query = ' '.join(context.args)
    results = await search_media(query)
    
    if not results:
        return await update.message.reply_text("❌ No matching results found")
    
    keyboard = []
    for item in results[:5]:
        btn_text = f"{item.title}"
        if item.type == 'series':
            btn_text += f" S{item.season:02d}E{item.episode:02d}"
        btn_text += f" ({item.quality})"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=item.file_id)])
    
    await update.message.reply_text(
        "🔍 Search Results:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def send_file(update: Update, _):
    query = update.callback_query
    file_id = query.data
    
    with Session(engine) as session:
        file = session.query(MediaFile).filter_by(file_id=file_id).first()
    
    await query.answer()
    await query.message.reply_video(
        video=file_id,
        caption=f"🎬 {file.title}\n"
                f"📺 Quality: {file.quality}\n"
                f"🔗 Direct Link: {file.caption}"
    )

# Indexing Function (Run once manually)
async def initial_indexing():
    from telethon.sync import TelegramClient
    
    client = TelegramClient(
        'bot_session',
        os.getenv("API_ID"),
        os.getenv("API_HASH")
    ).start(bot_token=TOKEN)
    
    async with client:
        async for message in client.iter_messages(CHANNEL_ID):
            if message.video or message.document:
                metadata = parse_caption(message.text)
                media = MediaFile(
                    file_id=message.file.id,
                    title=metadata['title'],
                    quality=detect_quality(message.text),
                    type=metadata.get('type', 'movie'),
                    season=metadata.get('season'),
                    episode=metadata.get('episode'),
                    caption=message.text
                )
                with Session(engine) as session:
                    session.merge(media)
                    session.commit()

if __name__ == '__main__':
    # Register Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('find', find))
    application.add_handler(CallbackQueryHandler(send_file))
    
    # Run Bot
    application.run_polling()
