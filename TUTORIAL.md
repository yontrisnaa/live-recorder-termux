# Tutorial Live Recorder — Install sampai Penggunaan

Panduan memakai Live Recorder di HP Android (Termux) dan VPS.

## 0. Ambil kode (git clone)
Repo ini **privat**, jadi butuh login sekali di Termux:
```bash
pkg install -y git gh
gh auth login
# pilih: GitHub.com → HTTPS → Yes → usado browser/kode yang muncul,
# buka github.com/login/device di HP, masukkan kode, izinkan
gh repo clone yontrisnaa/live-recorder-termux ~/termux
cd ~/termux
```
Tanpa `gh`, alternatif pakai token (ganti `TOKEN`):
```bash
git clone https://TOKEN@github.com/yontrisnaa/live-recorder-termux.git ~/termux
```
Update kode di lain waktu: `cd ~/termux && git pull`.

## 1. Syarat
- HP Android + aplikasi **Termux** (dari F-Droid, bukan Play Store versi lama)
- Koneksi internet, ruang kosong ±200MB per 20 menit rekaman

## 2. Install (sekali saja)
```bash
cd ~/termux
bash setup-termux.sh
```
Script memasang `python` + `ffmpeg` dan mengunci wake-lock agar HP tidak tidur.

## 3. Jalankan server + buka halaman
```bash
cd ~/termux
python3 live-proxy.py
```
Buka di Chrome HP: **http://localhost:8000/live-recorder-local.html**

> Kenapa perlu proxy? Server live menolak request tanpa Referer (error 403).
> Semua request halaman ini dilewatkan ke `/proxy` yang menyuntikkan Referer
> yang diizinkan secara otomatis.

## 4. Penggunaan

### Nonton
- Daftar **Sedang live** terisi otomatis tiap 15 detik (tombol ↻ untuk manual).
- Tiap baris ada badge 🆓 gratis / 🔒 harga + tombol **▶ Nonton** / **⏺ MP4**.
- Bisa juga tempel manual: URL halaman `/live/?streamId=...` atau URL `.m3u8`
  langsung, lalu **▶ Nonton**.

### Record
| Tombol | Hasil | Cocok untuk |
|---|---|---|
| ⏺ .ts → ⏹ → ⬇ .ts | Gabungan segmen `.ts` (bisa Suppabel) | Klip pendek, tanpa ffmpeg |
| ⏺ Record MP4 → ⏹ → ⬇ MP4 | MP4 via ffmpeg server, tanpa encode ulang | Hasil siap putar/bagikan |

### Auto-download (tanpa dibuka)
```bash
cd ~/termux
bash run-watcher.sh
```
Setiap ada live baru langsung direkam ke `rekaman/<waktu>_<judul>/seg_000.mp4...`
(per 5 menit). Cek `tail -f watcher.log`. Berhenti: `pkill -f watcher-termux.py`.
Pindahkan hasil berkala ke `~/storage/downloads` (aktifkan dulu
`termux-setup-storage`).

### Bot Telegram otomatis (opsional, butuh VPS)
`watcher.py` versi VPS memantau live dan **mengirim URL m3u8 ke Telegram**
saat live baru muncul (plus arsip URL agar live berbayar tetap terlacak).
Butuh `BOT_TOKEN` + `CHAT_ID`, dijalankan sebagai systemd service.

## 5. Masalah umum
| Gejala | Sebab & solusi |
|---|---|
| Playlist HTTP 403 | Request tanpa Referer — pastikan lewat halaman ini (proxy), bukan URL langsung |
| "terkunci, tanpa arsip" | Live berbayar & URL belum pernah terlihat gratis — tunggu unlock/arsip |
| Tidak ada live | Memang tidak ada siaran aktif — daftar kosong itu normal |
| HP berhenti merekam | Termux mati/tidur — jalankan `termux-wake-lock`, colok charger |
| `ffmpeg: command not found` | Ulangi `pkg install -y ffmpeg` |
