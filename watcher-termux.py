"""Auto-download live baru -> MP4 tersegment. Versi Termux (tanpa Telegram).
- Poll /api/lives tiap 20 dtk; live baru -> resolve hls_url -> ffmpeg.
- Live terkunci tanpa arsip -> dilewati. Arsip m3u8 disimpan (archive.json).
- Output: rekaman_<judul>_<waktu>/seg_000.mp4, ... (per 5 menit, masing2 playable).
Jalankan:  bash run-watcher.sh   (atau: nohup python3 watcher-termux.py >/dev/null 2>&1 &)
"""
import json
import os
import re
import subprocess
import time
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(BASE, "rekaman")
ARCHIVE = os.path.join(BASE, "archive.json")
LOGF = os.path.join(BASE, "watcher.log")
API = "https://mimigocell.online"
REFERER = "https://mimigocell.online/"
UA = ("Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Mobile Safari/537.36")
POLL = 20
MISS_LIMIT = 3
STALL_LIMIT = 5
SEG_TIME = 300


def log(m):
    line = time.strftime("%Y-%m-%d %H:%M:%S") + " " + m
    print(line, flush=True)
    try:
        with open(LOGF, "a") as f:
            f.write(line + "\n")
    except Exception:  # noqa: BLE001
        pass


def get(path):
    req = urllib.request.Request(API + path,
                                 headers={"Referer": REFERER, "User-Agent": UA,
                                          "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode())


def safe(s):
    s = re.sub(r"[^A-Za-z0-9_-]+", "_", s or "live")
    return s.strip("_")[:40] or "live"


def load_archive():
    try:
        with open(ARCHIVE) as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return {}


def save_archive(a):
    tmp = ARCHIVE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(a, f)
    os.replace(tmp, ARCHIVE)


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    archive = load_archive()
    active = {}
    log("watcher-termux jalan, OUTDIR=" + OUTDIR)
    while True:
        try:
            lives = get("/api/lives").get("data", [])
        except Exception as e:  # noqa: BLE001
            log("poll gagal: %s" % e)
            time.sleep(POLL)
            continue
        seen = set()
        for v in lives:
            sid = v.get("stream_id")
            if not sid:
                continue
            seen.add(sid)
            if sid in active:
                active[sid]["misses"] = 0
                continue
            try:
                d = get("/api/live/" + urllib.parse.quote(sid))
            except Exception as e:  # noqa: BLE001
                log("detail %s gagal: %s" % (sid, e))
                continue
            if d.get("hls_url"):
                archive[sid] = {"hls_url": d["hls_url"],
                                "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                                "title": d.get("title") or v.get("title")}
                save_archive(archive)
            url = d.get("hls_url") or (archive.get(sid) or {}).get("hls_url")
            if not url:
                log("live %s terkunci/tanpa arsip, dilewati" % sid)
                continue
            title = safe(v.get("title") or v.get("creator_name") or sid)
            folder = os.path.join(OUTDIR, "%s_%s" % (time.strftime("%Y%m%d-%H%M%S"), title))
            os.makedirs(folder, exist_ok=True)
            pat = os.path.join(folder, "seg_%03d.mp4")
            cmd = ["ffmpeg", "-y", "-loglevel", "warning",
                   "-headers", "Referer: " + REFERER,
                   "-i", url, "-c", "copy",
                   "-f", "segment", "-segment_time", str(SEG_TIME),
                   "-reset_timestamps", "1", pat]
            p = subprocess.Popen(cmd)
            active[sid] = {"proc": p, "folder": folder, "misses": 0,
                           "stall": 0, "lastsize": 0,
                           "title": title, "started": time.time()}
            log("REC START %s -> %s" % (sid, folder))
        done = []
        for sid, a in active.items():
            if sid not in seen:
                a["misses"] += 1
            try:
                cur = sum(os.path.getsize(os.path.join(a["folder"], f))
                          for f in os.listdir(a["folder"]) if f.endswith(".mp4"))
            except Exception:  # noqa: BLE001
                cur = a["lastsize"]
            if cur == a["lastsize"]:
                a["stall"] += 1
            else:
                a["stall"] = 0
                a["lastsize"] = cur
            dead = a["proc"].poll() is not None
            if a["misses"] >= MISS_LIMIT or a["stall"] >= STALL_LIMIT or dead:
                done.append(sid)
        for sid in done:
            a = active.pop(sid)
            if a["proc"].poll() is None:
                a["proc"].terminate()
                try:
                    a["proc"].wait(timeout=20)
                except Exception:  # noqa: BLE001
                    a["proc"].kill()
            n = len([f for f in os.listdir(a["folder"]) if f.endswith(".mp4")])
            mins = round((time.time() - a["started"]) / 60, 1)
            log("REC STOP %s (%s mnt, %d file) di %s" % (sid, mins, n, a["folder"]))
        time.sleep(POLL)


if __name__ == "__main__":
    main()
