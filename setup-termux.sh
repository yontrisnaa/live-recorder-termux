#!/bin/bash
# Setup sekali jalan di Termux, lalu jalankan servernya.
# Cara pakai:
#   1. Copy folder ini ke HP (mis. ~/termux)
#   2. Di Termux:  cd ~/termux && bash setup-termux.sh
#   3. Buka Chrome HP:  http://localhost:8000/live-recorder-local.html
set -e
pkg update -y
pkg install -y python ffmpeg
termux-wake-lock
echo ""
echo "OK. Sekarang jalankan:"
echo "  cd ~/termux && python3 live-proxy.py"
echo "Lalu buka di Chrome HP: http://localhost:8000/live-recorder-local.html"
echo "(Biarkan Termux tetap berjalan saat merekam.)"
