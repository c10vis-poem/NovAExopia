#!/usr/bin/env python3
"""FAKE TypeSafe endpoint for the selftest. Not the real API: it proves our client's handling, not Jev's answers.
It enforces the request shape from docs.typesafe.ai/api/system-one and answers in the documented response shape.
The first path segment picks the behaviour: /ok/v1/systemone, /http429/v1/systemone, ... Usage: fake_typesafe.py PORTFILE LOGFILE
"""
import json, sys, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

KEY = "fake-test-key"
def answer(level, group, others, lc=0.9, gc=0.9):
    probs = {str(i): (0.9 if i == level else 0.1 / 3) for i in range(4)}
    return {"model": "fake-jev-1.0", "usage": {"input_tokens": 9, "output_tokens": 2}, "answers": {
        "level": {"type": "score", "score": float(level), "confidence": lc, "legend": {}, "probabilities": probs},
        "group": {"type": "choice", "choice": group, "confidence": gc, "probabilities": {group: 0.7, **others}}}}

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def reply(self, code, data, headers=()):
        b = data if isinstance(data, bytes) else json.dumps(data).encode()
        self.send_response(code)
        for k, v in headers: self.send_header(k, v)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)
    def do_GET(self):
        with open(sys.argv[2], "a") as f: f.write(json.dumps({"method": "GET", "auth": self.headers.get("Authorization")}) + "\n")
        self.reply(405, {"detail": "method not allowed"})
    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        mode, _, rest = self.path.lstrip("/").partition("/")
        auth = self.headers.get("Authorization")
        with open(sys.argv[2], "a") as f: f.write(json.dumps({"path": self.path, "auth": auth, "body": raw.decode()}) + "\n")
        if rest != "v1/systemone": return self.reply(404, {"detail": "no such path"})
        if auth != "Bearer " + KEY: return self.reply(401, {"detail": "bad key"})
        try:
            b = json.loads(raw)
            q = b["questions"]
            assert b["model"] and isinstance(b["state"]["task"], str)
            assert q["level"]["type"] == "score" and 2 <= len(q["level"]["criteria"]) <= 10 and q["level"]["instructions"]
            assert q["group"]["type"] == "choice" and 2 <= len(q["group"]["criteria"]) <= 255 and q["group"]["instructions"]
        except (AssertionError, KeyError, TypeError, ValueError):
            return self.reply(422, {"detail": "bad body"})
        if mode == "ok": return self.reply(200, answer(2, "review", {"plan": 0.3}))
        if mode == "low": return self.reply(200, answer(1, "plan", {"review": 0.3}, 0.4, 0.3))
        if mode == "none": return self.reply(200, answer(0, "none_of_the_above", {"review": 0.1}))
        if mode == "garbage": return self.reply(200, b"not json at all")
        if mode == "unknown": return self.reply(200, answer(1, "not-a-real-group", {}))
        if mode == "slow":
            time.sleep(4)
            return self.reply(200, answer(2, "review", {}))
        if mode == "redirect": return self.reply(302, b"", [("Location", "/ok/v1/systemone")])
        if mode.startswith("http"): return self.reply(int(mode[4:]), {"detail": "fake error"})
        self.reply(500, {"detail": "unknown fake mode"})

s = ThreadingHTTPServer(("127.0.0.1", 0), H)
open(sys.argv[1], "w").write(str(s.server_port))
s.serve_forever()
