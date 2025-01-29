import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables (since we are not using .env, these can be set directly in Railway)
API_ID = int(os.getenv("28150346"))
API_HASH = os.getenv("426f0d0a1da02dea8fb71cb0bd3ab7e1")
BOT_TOKEN = os.getenv("6757464190:AAG7QlwzfP3wCwyOJ_nQN9K9836RJJaZchU")
MONGO_URL = os.getenv("mongodb+srv://captainstive1:wubabkU9rYHe9GAu@cluster0.bk3fq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")  # MongoDB Connection URL

# MongoDB Connection
client = MongoClient(MONGO_URL)
db = client["telegram_bot"]
source_channels = db["source_channels"]
destination_channel = db["destination_channel"]
