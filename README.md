# Telegram Channel Management Bot

यह एक Telegram bot है जो आपके channel को manage करने में मदद करता है। Bot authorized users को link post करने की अनुमति देता है और other admins द्वारा post किए गए links को automatically delete कर देता है।

## Features

- ✅ Channel monitoring और link deletion
- 🔐 Authorized user management
- 📝 Multiple channels support
- 🚀 Easy deployment
- 📊 Admin commands

## Setup Instructions

### 1. Prerequisites

```bash
# Python 3.x और pip होना जरूरी है
python3 --version
pip3 --version
```

### 2. Get Required Credentials

आपको निम्नलिखित credentials की जरूरत होगी:

1. **API_ID और API_HASH**: 
   - https://my.telegram.org/apps पर जाएं
   - एक new app create करें
   - API_ID और API_HASH copy करें

2. **BOT_TOKEN**: 
   - Telegram पर @BotFather को message करें
   - `/newbot` command use करें
   - Bot name और username set करें
   - Bot token copy करें

3. **OWNER_ID**: 
   - @userinfobot को message करें
   - आपका user ID मिल जाएगा

### 3. Environment Setup

```bash
# .env file create करें
cp .env.example .env

# .env file edit करें और अपने credentials add करें
nano .env
```

### 4. Deployment Options

#### Option A: Quick Start (Development)

```bash
# Dependencies install करें
pip3 install --break-system-packages -r requirements.txt

# Bot start करें
python3 run.py
```

#### Option B: Production Deployment (Systemd Service)

```bash
# Deployment script को executable बनाएं
chmod +x deploy.sh

# Deploy करें
./deploy.sh
```

### 5. Bot Commands

#### Owner/Authorized User Commands:

- `/start` - Welcome message और bot info
- `/help` - Help और commands list
- `/addchannel <channel_id>` - Channel add करें monitoring के लिए
- `/removechannel <channel_id>` - Channel remove करें
- `/showchannels` - Added channels की list
- `/authorizeuser <user_id>` - User को authorize करें
- `/unauthorizeuser <user_id>` - User authorization remove करें
- `/showauthorizedusers` - Authorized users की list
- `/postlink <text> <link>` - Channels में link post करें
- `/testadmin <user_id>` - Check if user is admin in channel

#### Examples:

```
/addchannel -1001234567890
/authorizeuser 123456789
/postlink "Check this out!" https://example.com
```

## How It Works

1. Bot authorized users के द्वारा posted links को allow करता है
2. Other channel admins के द्वारा posted links को 5 seconds में delete कर देता है
3. Authorized users commands के through multiple channels में links post कर सकते हैं

## Service Management (Production)

```bash
# Status check करें
sudo systemctl status telegram-bot

# Bot stop करें
sudo systemctl stop telegram-bot

# Bot start करें
sudo systemctl start telegram-bot

# Bot restart करें
sudo systemctl restart telegram-bot

# Logs देखें
sudo journalctl -u telegram-bot -f
```

## Troubleshooting

### Common Issues:

1. **"Permission denied" errors**: 
   - Make sure you have sudo access
   - Check file permissions

2. **"Module not found" errors**: 
   - Ensure dependencies are installed: `pip3 install --break-system-packages telethon`

3. **Bot not responding**: 
   - Check if credentials are correct in .env
   - Verify bot token with @BotFather
   - Check service logs: `sudo journalctl -u telegram-bot -f`

4. **Links not getting deleted**: 
   - Make sure bot has admin permissions in the channel
   - Check if channel ID is correctly added
   - Verify bot is added to the channel

### Getting Help

अगर कोई problem आए तो:
1. Service logs check करें
2. .env file में credentials verify करें
3. Bot को channel में admin बनाना न भूलें

## Security Note

- .env file को कभी भी public repository में upload न करें
- Credentials को secure रखें
- Bot को sirf trusted channels में admin बनाएं

## License

This project is for educational purposes. Use responsibly!
