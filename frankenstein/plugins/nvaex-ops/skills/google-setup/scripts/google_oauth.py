#!/usr/bin/env python3
"""Create or refresh a Google token file for claw-mcp's Google route. Standard library only.

  google_oauth.py check [--dir DIR]
      List token files in DIR (default $CLAW_GOOGLE_DIR or ~/.config/claw-mcp): account, mode, which keys exist.
      Never prints a value.
  google_oauth.py login ACCOUNT --client-file client_secret.json [--dir DIR] [--scopes drive,gmail,calendar] [--no-browser]
      Loopback OAuth for a "Desktop app" client. Prints a consent URL, waits on 127.0.0.1 for Google's redirect,
      exchanges the code, writes DIR/google-ACCOUNT.json with mode 600: {client_id, client_secret, refresh_token}.
      The client id/secret may come from env CLAW_GOOGLE_CLIENT_ID / CLAW_GOOGLE_CLIENT_SECRET instead of --client-file.
      Re-running for the same account replaces the token (that is the re-consent / reauth step).

Why loopback and not the device-code flow: Google's device flow does not allow the Drive, Gmail or Calendar scopes.
Tokens, secrets and the auth code are never printed or logged. The consent URL holds only the public client id.
"""
import http.server, json, os, secrets, socket, stat, sys, threading, urllib.parse, urllib.request, urllib.error, subprocess, shutil, re, hashlib, base64

SCOPES = {  # least needed for claw's ops: read Drive, create Drive files, read Gmail, create drafts, Calendar
    "drive": ["https://www.googleapis.com/auth/drive.readonly", "https://www.googleapis.com/auth/drive.file"],
    "gmail": ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.compose"],
    "calendar": ["https://www.googleapis.com/auth/calendar"],
}
AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN = "https://oauth2.googleapis.com/token"

def outdir(a):
    return a or os.environ.get("CLAW_GOOGLE_DIR") or os.path.join(os.path.expanduser("~"), ".config", "claw-mcp")

def cmd_check(args):
    d = outdir(opt(args, "--dir"))
    if not os.path.isdir(d):
        print(f"no token folder at {d}"); return 1
    n = 0
    for f in sorted(os.listdir(d)):
        m = re.fullmatch(r"google-([\w.@+-]+)\.json", f)
        if not m: continue
        p = os.path.join(d, f); mode = stat.S_IMODE(os.stat(p).st_mode)
        try: keys = sorted(json.load(open(p)).keys())
        except Exception: keys = ["(not valid JSON)"]
        warn = "" if not mode & 0o077 else "  REFUSED by claw: run chmod 600"
        print(f"{m.group(1)}: mode {mode:o}, keys {','.join(keys)}{warn}"); n += 1
    if not n: print(f"no google-<account>.json files in {d}")
    return 0 if n else 1

def opt(args, name):
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else None

def load_client(path):
    cid, sec = os.environ.get("CLAW_GOOGLE_CLIENT_ID"), os.environ.get("CLAW_GOOGLE_CLIENT_SECRET")
    if path:
        j = json.load(open(path)); j = j.get("installed") or j.get("web") or j
        cid, sec = j.get("client_id"), j.get("client_secret")
    if not cid:
        sys.exit("no OAuth client: pass --client-file or set CLAW_GOOGLE_CLIENT_ID and CLAW_GOOGLE_CLIENT_SECRET")
    return cid, sec or ""

def post(url, data):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, urllib.parse.urlencode(data).encode()), timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        try: j = json.load(e)
        except Exception: j = {}
        sys.exit(f"token endpoint HTTP {e.code}: {j.get('error')} {j.get('error_description', '')}")

def cmd_login(args):
    if not args or args[0].startswith("-"): sys.exit("usage: login ACCOUNT --client-file FILE")
    acct = args[0]
    if not re.fullmatch(r"[\w.@+-]+", acct) or ".." in acct: sys.exit("bad account name")
    cid, sec = load_client(opt(args, "--client-file"))
    names = (opt(args, "--scopes") or "drive,gmail,calendar").split(",")
    if any(n not in SCOPES for n in names): sys.exit("scopes must be from: " + ",".join(SCOPES))
    scope = " ".join(s for n in names for s in SCOPES[n])
    # Test hook: only a loopback token endpoint may replace Google's, so no env var can send the secret elsewhere.
    token_url = os.environ.get("GOOGLE_OAUTH_TOKEN_URL", TOKEN)
    if token_url != TOKEN and not re.match(r"http://127\.0\.0\.1:\d+/", token_url): sys.exit("GOOGLE_OAUTH_TOKEN_URL must be http://127.0.0.1")
    state = secrets.token_urlsafe(24); verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    got = {}; done = threading.Event()
    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if q.get("state", [""])[0] == state and ("code" in q or "error" in q):
                got.update({k: v[0] for k, v in q.items()}); done.set()
                self.send_response(200); self.send_header("Content-Type", "text/plain"); self.end_headers()
                self.wfile.write(b"Done. You can close this tab and return to the terminal.\n")
            else:
                self.send_response(404); self.end_headers()
        def log_message(self, *a): pass
    srv = http.server.HTTPServer(("127.0.0.1", 0), H); port = srv.server_address[1]
    redirect = f"http://127.0.0.1:{port}/"
    url = AUTH + "?" + urllib.parse.urlencode({"client_id": cid, "redirect_uri": redirect, "response_type": "code", "scope": scope,
          "access_type": "offline", "prompt": "consent", "state": state, "code_challenge": challenge, "code_challenge_method": "S256"})
    print(f"Open this URL in the phone's browser and approve account '{acct}':\n{url}\n(waiting up to 5 minutes on {redirect})", file=sys.stderr)
    if "--no-browser" not in args and shutil.which("termux-open-url"):
        subprocess.run(["termux-open-url", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t = threading.Thread(target=srv.serve_forever, daemon=True); t.start()
    ok = done.wait(300); srv.shutdown(); srv.server_close()
    if not ok: sys.exit("timed out waiting for consent")
    if "error" in got: sys.exit("consent refused: " + got["error"])
    tok = post(token_url, {"code": got["code"], "client_id": cid, "client_secret": sec, "redirect_uri": redirect,
                           "grant_type": "authorization_code", "code_verifier": verifier})
    rt = tok.get("refresh_token")
    if not rt: sys.exit("Google returned no refresh_token (revoke the app at myaccount.google.com/permissions, then log in again)")
    d = outdir(opt(args, "--dir")); os.makedirs(d, mode=0o700, exist_ok=True)
    p = os.path.join(d, f"google-{acct}.json")
    fd = os.open(p + ".tmp", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f: json.dump({"client_id": cid, "client_secret": sec, "refresh_token": rt}, f)
    os.chmod(p + ".tmp", 0o600); os.replace(p + ".tmp", p)
    print(f"wrote {p} (mode 600). Scopes: {', '.join(names)}.")
    return 0

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] not in ("check", "login"): print(__doc__); sys.exit(2)
    sys.exit((cmd_check if a[0] == "check" else cmd_login)(a[1:]))
