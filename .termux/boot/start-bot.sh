#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
cd ~/paper-trading-bot
nohup python3 -u tab_loop.py > bot.log 2>&1 &
