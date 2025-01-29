import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables (since we are not using .env, these can be set directly in Railway)
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")  # MongoDB Connection URL

# MongoDB Connection
client = MongoClient(MONGO_URL)
db = client["telegram_bot"]
source_channels = db["source_channels"]
destination_channel = db["destination_channel"]
