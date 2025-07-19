# main.py - Replit Entry Point
import subprocess
import sys
import os

print("🚀 Starting Telegram Bot on Replit...")

# Install dependencies if not already installed
try:
    import telethon
    print("✅ Dependencies already installed")
except ImportError:
    print("📦 Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("✅ Dependencies installed")

# Check environment variables
required_vars = ['API_ID', 'API_HASH', 'BOT_TOKEN', 'OWNER_ID']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
    print("Please set them in Replit's Environment Variables tab or .env file")
    sys.exit(1)

print("✅ Environment variables found")
print("🤖 Starting bot...")

# Import and run the bot
import bot_with_keepalive