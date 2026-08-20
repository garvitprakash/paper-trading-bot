#!/data/data/com.termux/files/usr/bin/bash
source ~/.bashrc
cd ~/paper-trading-bot
if pgrep -f tab_loop.py > /dev/null; then
    echo "Already running"
else
    termux-wake-lock
    nohup python3 -u tab_loop.py > bot.log 2>&1 &
    echo "Bot start ho gaya"
fi