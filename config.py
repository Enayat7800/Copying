import os
from pymongo import MongoClient

# MongoDB connection
client = MongoClient(os.getenv('mongodb+srv://captainstive1:wubabkU9rYHe9GAu@cluster0.bk3fq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'))
db = client['telegram_bot']
source_channels = db['source_channels']
destination_channel = db['destination_channel']

# Telegram Bot API credentials
API_ID = os.getenv('28150346')
API_HASH = os.getenv('426f0d0a1da02dea8fb71cb0bd3ab7e1')
BOT_TOKEN = os.getenv('6757464190:AAG7QlwzfP3wCwyOJ_nQN9K9836RJJaZchU')
