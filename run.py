#!/usr/bin/env python3
"""
Simple runner script for the Telegram bot that loads environment variables from .env file
"""
import os
import sys
from pathlib import Path

def load_env_file():
    """Load environment variables from .env file"""
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ .env file not found!")
        print("📋 Please copy .env.example to .env and fill in your credentials:")
        print("   cp .env.example .env")
        print("   nano .env")
        print("")
        print("🔑 You need these credentials:")
        print("   - API_ID and API_HASH from https://my.telegram.org/apps")
        print("   - BOT_TOKEN from @BotFather")
        print("   - OWNER_ID (your Telegram user ID from @userinfobot)")
        sys.exit(1)
    
    # Load variables from .env file
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
    
    # Check if all required variables are set
    required_vars = ['API_ID', 'API_HASH', 'BOT_TOKEN', 'OWNER_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file and ensure all variables are set.")
        sys.exit(1)
    
    print("✅ Environment variables loaded successfully")

if __name__ == "__main__":
    print("🚀 Starting Telegram Bot...")
    load_env_file()
    
    # Now import and run the bot
    try:
        import bot
        print("🤖 Bot started successfully!")
    except ImportError as e:
        print(f"❌ Failed to import bot module: {e}")
        print("Make sure telethon is installed: pip3 install telethon")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        sys.exit(1)