#!/bin/bash
# Jalankan auto-download di background (Termux).
# Berhentikan:  pkill -f watcher-termux.py
cd "$(dirname "$0")"
termux-wake-lock
nohup python3 watcher-termux.py > watcher-out.log 2>&1 &
echo "watcher jalan (PID $!). Log: tail -f watcher.log"
echo "Hasil: folder rekaman/"
