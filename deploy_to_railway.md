# 🚆 Railway Deployment Guide

## Railway पर 24/7 Free Hosting

### Step 1: GitHub Repository बनाएं

```bash
# Git initialize करें
git init
git add .
git commit -m "Initial commit"

# GitHub पर repository बनाएं और push करें
git remote add origin https://github.com/yourusername/telegram-bot.git
git push -u origin main
```

### Step 2: Railway Account Setup

1. https://railway.app पर जाएं
2. GitHub से sign up करें
3. "Deploy from GitHub repo" select करें
4. अपनी repository select करें

### Step 3: Environment Variables Set करें

Railway dashboard में:
```
API_ID = 28150346
API_HASH = 426f0d0a1da02dea8fb71cb0bd3ab7e1
BOT_TOKEN = 7540024639:AAFHcQ5YuIOyNIZsKKgRrfw4nj5p-3s2WxU
OWNER_ID = 1251962299
```

### Step 4: Deploy

- Railway automatically detect करेगा Python app
- Deploy button पर click करें
- Bot automatically start हो जाएगा

## ✅ Benefits:

- **500 free hours per month**
- **Automatic restarts**
- **24/7 uptime**
- **No sleep mode**
- **Free domain**

## 📊 Usage Monitoring:

Railway dashboard में आप dekh सकते हैं:
- CPU usage
- Memory usage
- Logs
- Deployment status

## 🔄 Auto-restart:

अगर bot crash हो जाए तो automatically restart हो जाएगा।

## 🆓 Free Tier Limits:

- **500 execution hours/month**
- **1GB RAM**
- **1GB disk space**
- **Fair use policy**

यह normal bot के लिए काफी है!