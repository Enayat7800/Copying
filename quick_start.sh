#!/bin/bash

echo "🚀 Quick Start - Telegram Bot"
echo "================================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo ""
    echo "📋 Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "✅ .env file created! Please edit it with your credentials:"
    echo ""
    echo "🔑 Required credentials:"
    echo "   1. API_ID and API_HASH from https://my.telegram.org/apps"
    echo "   2. BOT_TOKEN from @BotFather"
    echo "   3. OWNER_ID (your Telegram user ID from @userinfobot)"
    echo ""
    echo "📝 Edit the .env file now:"
    echo "   nano .env"
    echo ""
    echo "⚡ After editing, run this script again to start the bot"
    exit 1
fi

# Load environment variables to check if they're set
source .env

# Check if all required variables are set
if [ -z "$API_ID" ] || [ "$API_ID" = "your_api_id_here" ] || \
   [ -z "$API_HASH" ] || [ "$API_HASH" = "your_api_hash_here" ] || \
   [ -z "$BOT_TOKEN" ] || [ "$BOT_TOKEN" = "your_bot_token_here" ] || \
   [ -z "$OWNER_ID" ] || [ "$OWNER_ID" = "your_user_id_here" ]; then
    echo "❌ Please update your .env file with real credentials!"
    echo ""
    echo "📝 Edit the .env file:"
    echo "   nano .env"
    echo ""
    echo "🔑 Make sure to replace all placeholder values with real ones"
    exit 1
fi

echo "✅ Environment variables found"

# Check dependencies
echo "📦 Checking dependencies..."
python3 -c "import telethon" 2>/dev/null || {
    echo "❌ Installing telethon..."
    pip3 install --break-system-packages telethon
}

echo "✅ Dependencies ready"
echo ""
echo "🤖 Starting Telegram Bot..."
echo "💡 Press Ctrl+C to stop the bot"
echo ""

# Start the bot
python3 run.py