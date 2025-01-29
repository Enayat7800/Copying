# Telegram Channel Copy Bot

This is a Telegram bot that copies messages and photos from specified source channels and posts them to a target channel.

## Setup

1.  Create a new bot using @BotFather and get your bot token.
2.  Create a `.env` file based on `.env.example` and replace the placeholder values with your actual bot token, target channel ID, and allowed user IDs.
3.  Install the required Python packages using `pip install -r requirements.txt`.
4.  Run the bot using `python bot.py`.

## Commands

-   `/start`: Start the bot.
-   `/addchannel <channel_id>`: Add a source channel.
-   `/removechannel <channel_id>`: Remove a source channel.
-   `/listchannels`: List all connected source channels.

## Deployment
To deploy the bot to railway follow these steps:
1. Create a GitHub repository and push this code to it
2. Create a new railway app and connect it with you GitHub repo.
3. Add the necessary environment variables (BOT_TOKEN, TARGET_CHANNEL_ID, ALLOWED_USERS) to railway.
4. Deploy the application.
