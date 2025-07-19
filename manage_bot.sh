#!/bin/bash

# Telegram Bot Management Script

case "$1" in
    start)
        echo "🚀 Starting Telegram Bot..."
        if ps aux | grep "python3 run.py" | grep -v grep > /dev/null; then
            echo "⚠️  Bot is already running!"
            ps aux | grep "python3 run.py" | grep -v grep
        else
            nohup python3 run.py > bot.log 2>&1 &
            sleep 2
            if ps aux | grep "python3 run.py" | grep -v grep > /dev/null; then
                echo "✅ Bot started successfully!"
                echo "📊 Process: $(ps aux | grep "python3 run.py" | grep -v grep)"
            else
                echo "❌ Failed to start bot. Check bot.log for errors."
            fi
        fi
        ;;
    stop)
        echo "🛑 Stopping Telegram Bot..."
        PID=$(ps aux | grep "python3 run.py" | grep -v grep | awk '{print $2}')
        if [ -n "$PID" ]; then
            kill $PID
            sleep 2
            if ps aux | grep "python3 run.py" | grep -v grep > /dev/null; then
                echo "⚠️  Bot still running, force killing..."
                kill -9 $PID
            fi
            echo "✅ Bot stopped successfully!"
        else
            echo "⚠️  Bot is not running!"
        fi
        ;;
    restart)
        echo "🔄 Restarting Telegram Bot..."
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        echo "📊 Bot Status:"
        if ps aux | grep "python3 run.py" | grep -v grep > /dev/null; then
            echo "✅ Bot is running:"
            ps aux | grep "python3 run.py" | grep -v grep
            echo ""
            echo "📝 Recent logs:"
            tail -10 bot.log 2>/dev/null || echo "No logs available"
        else
            echo "❌ Bot is not running!"
        fi
        ;;
    logs)
        echo "📝 Bot Logs (Press Ctrl+C to exit):"
        tail -f bot.log
        ;;
    *)
        echo "🤖 Telegram Bot Management"
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the bot"
        echo "  stop    - Stop the bot"
        echo "  restart - Restart the bot"
        echo "  status  - Show bot status"
        echo "  logs    - Show live logs"
        echo ""
        echo "Examples:"
        echo "  $0 start"
        echo "  $0 status"
        echo "  $0 logs"
        exit 1
        ;;
esac