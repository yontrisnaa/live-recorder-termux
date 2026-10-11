# Live Recorder (Termux)

Nonton + rekam live HLS otomatis dari HP Android (Termux).

## Isi
- `live-recorder-local.html` — halaman studio: daftar live otomatis, nonton, record `.ts`/MP4
- `live-proxy.py` — server lokal + proxy penyuntik Referer + endpoint record MP4
- `watcher-termux.py` — auto-download tiap ada live baru ke folder `rekaman/`
- `setup-termux.sh` / `run-watcher.sh` — setup & jalan sekali perintah

## Pakai
```bash
cd ~/termux && bash setup-termux.sh
python3 live-proxy.py
# buka Chrome HP: http://localhost:8000/live-recorder-local.html
bash run-watcher.sh   # auto-download (opsional)
```
