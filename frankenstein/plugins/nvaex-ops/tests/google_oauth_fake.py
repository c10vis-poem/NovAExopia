#!/usr/bin/env python3
"""Drive google_oauth.py login against a fake token endpoint on 127.0.0.1 and a fake browser (a GET to the redirect).
Proves: URL has PKCE+state, token file written 0600 with the right keys, no secret value appears in output, reauth replaces the file."""
import http.server, json, os, re, stat, subprocess, sys, tempfile, threading, urllib.parse, urllib.request
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills", "google-setup", "scripts", "google_oauth.py")
seen = {}
class T(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        seen.update({k: v[0] for k, v in urllib.parse.parse_qs(self.rfile.read(int(self.headers["Content-Length"])).decode()).items()})
        b = json.dumps({"access_token": "ACCESS-FAKE-1", "refresh_token": "REFRESH-FAKE-%d" % seen.get("n", 0), "expires_in": 3600}).encode()
        self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def log_message(self, *a): pass
srv = http.server.HTTPServer(("127.0.0.1", 0), T); threading.Thread(target=srv.serve_forever, daemon=True).start()
d = tempfile.mkdtemp()
env = dict(os.environ, GOOGLE_OAUTH_TOKEN_URL="http://127.0.0.1:%d/token" % srv.server_address[1],
           CLAW_GOOGLE_CLIENT_ID="cid.apps.example", CLAW_GOOGLE_CLIENT_SECRET="CLIENT-SECRET-FAKE")
def run_login():
    p = subprocess.Popen([sys.executable, "-I", S, "login", "me", "--dir", d, "--no-browser"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    url = None
    while True:
        line = p.stderr.readline()
        if line.startswith("http"): url = line.strip(); break
        if not line: break
    assert url, "no consent URL printed"
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    assert q["code_challenge_method"] == ["S256"] and q["access_type"] == ["offline"] and q["state"], q
    assert "gmail.compose" in q["scope"][0] and "drive.file" in q["scope"][0]
    try: urllib.request.urlopen(q["redirect_uri"][0] + "?code=X&state=wrong", timeout=5); raise SystemExit("wrong state accepted")
    except urllib.error.HTTPError as e: assert e.code == 404
    urllib.request.urlopen(q["redirect_uri"][0] + "?code=CODE-FAKE&state=" + q["state"][0], timeout=5).read()
    out, err = p.communicate(timeout=20)
    assert p.returncode == 0, (out, err)
    for secret in ("CLIENT-SECRET-FAKE", "REFRESH-FAKE", "ACCESS-FAKE", "CODE-FAKE"):
        assert secret not in out + err + url, "secret leaked: " + secret
    return q
q = run_login()
f = os.path.join(d, "google-me.json")
assert stat.S_IMODE(os.stat(f).st_mode) == 0o600
j = json.load(open(f)); assert sorted(j) == ["client_id", "client_secret", "refresh_token"], j
assert seen["grant_type"] == "authorization_code" and seen["code"] == "CODE-FAKE" and seen["code_verifier"]
seen["n"] = 2; run_login(); assert json.load(open(f))["refresh_token"] == "REFRESH-FAKE-2", "reauth did not replace the token"
chk = subprocess.run([sys.executable, "-I", S, "check", "--dir", d], capture_output=True, text=True)
assert "me: mode 600" in chk.stdout and "FAKE" not in chk.stdout, chk.stdout
print("google_oauth fake flow ok")
