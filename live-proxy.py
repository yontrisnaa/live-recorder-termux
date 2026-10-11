"""Proxy lokal untuk live-recorder: menyuntik Referer yang diizinkan + CORS.
Jalankan:  python3 live-proxy.py   ->  buka http://localhost:8000/live-recorder-local.html
"""
import http.server
import json
import os
import subprocess
import time
import urllib.parse
import urllib.request

PORT = 8000
ROOT = os.path.dirname(os.path.abspath(__file__))
ALLOW_REFERER = "https://mimigocell.online/"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

JOBS = {}
JOB_SEQ = [0]


def jresp(s, obj, code=200):
    body = json.dumps(obj).encode()
    s.send_response(code)
    s.send_header("Content-Type", "application/json")
    s.send_header("Access-Control-Allow-Origin", "*")
    s.send_header("Content-Length", str(len(body)))
    s.end_headers()
    s.wfile.write(body)


class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/proxy":
            q = urllib.parse.parse_qs(u.query)
            t = (q.get("url") or [None])[0]
            if not t:
                self.send_error(400, "param url wajib")
                return
            req = urllib.request.Request(
                t, headers={"Referer": ALLOW_REFERER, "User-Agent": UA})
            try:
                r = urllib.request.urlopen(req, timeout=25)
            except Exception as e:  # noqa: BLE001
                self.send_error(502, str(e))
                return
            body = r.read()
            ct = r.headers.get("Content-Type", "application/octet-stream")
            if "mpegurl" in ct or "m3u8" in t:
                out = []
                for ln in body.decode("utf-8", "ignore").split("\n"):
                    s = ln.strip()
                    if s and not s.startswith("#") and ".ts" in s:
                        absu = urllib.parse.urljoin(t, s)
                        ln = "/proxy?url=" + urllib.parse.quote(absu, safe="")
                    out.append(ln)
                body = "\n".join(out).encode()
                ct = "application/vnd.apple.mpegurl"
            self.send_response(200)
            self.send_header("Content-Type", ct)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if u.path == "/rec-start":
            q = urllib.parse.parse_qs(u.query)
            t = (q.get("url") or [None])[0]
            if not t:
                self.send_error(400, "param url wajib")
                return
            JOB_SEQ[0] += 1
            jid = str(int(time.time())) + "_" + str(JOB_SEQ[0])
            out = os.path.join(ROOT, "rec_" + jid + ".mp4")
            cmd = ["ffmpeg", "-y", "-loglevel", "warning",
                   "-headers", "Referer: " + ALLOW_REFERER,
                   "-i", t, "-c", "copy", out]
            try:
                p = subprocess.Popen(cmd)
            except Exception as e:  # noqa: BLE001
                self.send_error(500, "ffmpeg: " + str(e))
                return
            JOBS[jid] = {"proc": p, "file": out, "url": t,
                         "started": time.time()}
            jresp(self, {"job": jid, "file": os.path.basename(out)})
            return
        if u.path == "/rec-status":
            q = urllib.parse.parse_qs(u.query)
            jid = (q.get("job") or [None])[0]
            j = JOBS.get(jid)
            if not j:
                self.send_error(404, "job tidak ada")
                return
            running = j["proc"].poll() is None
            size = os.path.getsize(j["file"]) if os.path.exists(j["file"]) else 0
            jresp(self, {"job": jid, "running": running,
                         "size": size, "elapsed": round(time.time() - j["started"], 1)})
            return
        if u.path == "/rec-stop":
            q = urllib.parse.parse_qs(u.query)
            jid = (q.get("job") or [None])[0]
            j = JOBS.get(jid)
            if not j:
                self.send_error(404, "job tidak ada")
                return
            if j["proc"].poll() is None:
                j["proc"].terminate()
                try:
                    j["proc"].wait(timeout=15)
                except Exception:  # noqa: BLE001
                    j["proc"].kill()
            size = os.path.getsize(j["file"]) if os.path.exists(j["file"]) else 0
            jresp(self, {"job": jid, "running": False, "size": size,
                         "file": os.path.basename(j["file"])})
            return
        if u.path == "/rec-dl":
            q = urllib.parse.parse_qs(u.query)
            jid = (q.get("job") or [None])[0]
            j = JOBS.get(jid)
            if not j or not os.path.exists(j["file"]):
                self.send_error(404, "file tidak ada")
                return
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(os.path.getsize(j["file"])))
            self.send_header("Content-Disposition",
                             'attachment; filename="%s"' % os.path.basename(j["file"]))
            self.end_headers()
            with open(j["file"], "rb") as f:
                while True:
                    b = f.read(65536)
                    if not b:
                        break
                    self.wfile.write(b)
            return
        return super().do_GET()


if __name__ == "__main__":
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H)
    print(f"live-proxy jalan di http://localhost:{PORT}/live-recorder-local.html")
    srv.serve_forever()
