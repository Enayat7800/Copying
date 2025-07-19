#!/bin/bash

# Telegram Bot Deployment Script

echo "🚀 Starting Telegram Bot Deployment..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "📋 Please copy .env.example to .env and fill in your credentials:"
    echo "   cp .env.example .env"
    echo "   nano .env"
    echo ""
    echo "🔑 You need these credentials:"
    echo "   - API_ID and API_HASH from https://my.telegram.org/apps"
    echo "   - BOT_TOKEN from @BotFather"
    echo "   - OWNER_ID (your Telegram user ID from @userinfobot)"
    exit 1
fi

# Load environment variables
echo "📁 Loading environment variables..."
export $(cat .env | grep -v '#' | xargs)

# Check if all required variables are set
if [ -z "$API_ID" ] || [ -z "$API_HASH" ] || [ -z "$BOT_TOKEN" ] || [ -z "$OWNER_ID" ]; then
    echo "❌ Missing required environment variables!"
    echo "Please check your .env file and ensure all variables are set."
    exit 1
fi

echo "✅ Environment variables loaded successfully"

# Check if Python dependencies are installed
echo "📦 Checking dependencies..."
python3 -c "import telethon" 2>/dev/null || {
    echo "❌ Telethon not found! Installing dependencies..."
    pip3 install --break-system-packages -r requirements.txt
}

echo "✅ Dependencies verified"

# Create a systemd service file for production deployment
echo "⚙️  Creating systemd service..."
sudo tee /etc/systemd/system/telegram-bot.service > /dev/null <<EOF
[Unit]
Description=Telegram Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=API_ID=$API_ID
Environment=API_HASH=$API_HASH
Environment=BOT_TOKEN=$BOT_TOKEN
Environment=OWNER_ID=$OWNER_ID
ExecStart=/usr/bin/python3 $(pwd)/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start the service
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

echo "▶️  Starting bot service..."
sudo systemctl start telegram-bot

echo "🔧 Enabling auto-start on boot..."
sudo systemctl enable telegram-bot

# Show service status
echo "📊 Service Status:"
sudo systemctl status telegram-bot --no-pager

echo ""
echo "🎉 Bot deployed successfully!"
echo ""
echo "📋 Useful commands:"
echo "   sudo systemctl status telegram-bot    # Check status"
echo "   sudo systemctl stop telegram-bot      # Stop bot"
echo "   sudo systemctl start telegram-bot     # Start bot"
echo "   sudo systemctl restart telegram-bot   # Restart bot"
echo "   sudo journalctl -u telegram-bot -f    # View logs"
echo ""
echo "💡 Your bot should now be running! Send /start to your bot on Telegram to test."