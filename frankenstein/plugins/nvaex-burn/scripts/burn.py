#!/usr/bin/env python3
"""nvaex-burn: usage pacer. Brake near the limit, burn pre-approved jobs near reset. Stdlib only.
Subcommands: status | tick [--dry-run] | hook | keepalive [--once] | notify MSG
Env: BURN_QUEUE (burn-queue.md path), BURN_USAGE_FILE / BURN_USAGE_CMD (usage reader),
     BURN_WEBHOOK_URL (notify; off if unset), BURN_PING_CMD (keep-alive ping; log-only if unset),
     BURN_STATE (state dir), BURN_NOW (epoch override, tests)."""
import json, os, shlex, subprocess, sys, time, urllib.request

H = os.path.expanduser("~")
STATE = os.environ.get("BURN_STATE", f"{H}/.claude/state/nvaex-burn")
QUEUE = os.environ.get("BURN_QUEUE", f"{H}/storage/shared/Documents/NovAExorpus/burn-queue.md")
USAGE_FILE = os.environ.get("BURN_USAGE_FILE", f"{H}/.claude/heavy-usage/usage-live.json")
BRAKE5, BRAKE7 = 90, 95          # % used: 5h / 7d
MIN_LEFT = 25                    # % unused needed to burn
TIERS = [("inferno", 6), ("blaze", 24), ("smoulder", 72)]  # hottest first, hours before reset
IDX = {t: i for i, (t, _) in enumerate(TIERS)}
STALE = 1800                     # usage reading older than this = unknown
ACTIVE = 1800                    # session counts as active this long after last prompt
KEEPALIVE = 270                  # 4m30s


def now():
    return float(os.environ.get("BURN_NOW") or time.time())


def log(msg):
    os.makedirs(STATE, exist_ok=True)
    with open(f"{STATE}/burn.log", "a") as f:
        f.write(f"{time.strftime('%F %T')} {msg}\n")


def read_usage():
    """Pluggable reader. Returns {five_hour:{used_percentage,resets_at}, seven_day:{...}} or None (unknown).
    BURN_USAGE_CMD prints that JSON; default reads the heavy-usage statusline capture file."""
    try:
        cmd = os.environ.get("BURN_USAGE_CMD")
        if cmd:
            d = json.loads(subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=20).stdout)
        else:
            d = json.load(open(USAGE_FILE))
        cap = d.get("capturedAt")
        if cap and now() - cap / 1000 > STALE:
            return None
        if not (d.get("five_hour") or d.get("seven_day")):
            return None
        return d
    except Exception:
        return None


def assess(u):
    """-> {mode: unknown|brake|burn|idle, tier, left, hours, why}"""
    if not u:
        return {"mode": "unknown", "why": "no usage source; nothing burns, nothing brakes"}
    f, s = u.get("five_hour") or {}, u.get("seven_day") or {}
    if f.get("used_percentage", 0) >= BRAKE5 or s.get("used_percentage", 0) >= BRAKE7:
        return {"mode": "brake", "why": f"5h {f.get('used_percentage')}% / 7d {s.get('used_percentage')}% used"}
    if s.get("used_percentage") is None or not s.get("resets_at"):
        return {"mode": "idle", "why": "no weekly figures"}
    left, hours = 100 - s["used_percentage"], (s["resets_at"] - now()) / 3600
    if hours <= 0 or left < MIN_LEFT:
        return {"mode": "idle", "left": left, "hours": round(hours, 1), "why": "outside burn window"}
    for tier, h in TIERS:
        if hours <= h:
            return {"mode": "burn", "tier": tier, "left": left, "hours": round(hours, 1), "why": f"{tier}: {left:.0f}% unused, {hours:.1f}h to reset"}
    return {"mode": "idle", "left": left, "hours": round(hours, 1), "why": ">72h to reset"}


def jobs():
    """Queue lines: '- [x] <tier> | <id> | <command>'. [x] = pre-approved; [ ] never runs. Vault is read-only here."""
    out = []
    try:
        for ln in open(QUEUE):
            ln = ln.strip()
            if ln.startswith("- [x]"):
                p = [x.strip() for x in ln[5:].split("|", 2)]
                if len(p) == 3 and p[0].lower() in IDX:
                    out.append({"tier": p[0].lower(), "id": p[1], "cmd": p[2]})
    except OSError:
        pass
    return out


def done():
    try:
        return set(open(f"{STATE}/done").read().split())
    except OSError:
        return set()


def notify(msg):
    url = os.environ.get("BURN_WEBHOOK_URL")
    if not url:
        return False
    try:
        req = urllib.request.Request(url, json.dumps({"text": msg}).encode(), {"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5)
        return True
    except Exception as e:
        log(f"notify failed: {e}")
        return False


def tick(dry):
    a = assess(read_usage())
    os.makedirs(STATE, exist_ok=True)
    brake = f"{STATE}/brake"
    if a["mode"] == "brake":
        if not os.path.exists(brake):
            open(brake, "w").write(a["why"])
            notify(f"nvaex-burn BRAKE: {a['why']}. Run /nvaex-burn:sweep.")
            log("brake on: " + a["why"])
    elif os.path.exists(brake):
        os.remove(brake)
        log("brake off")
    ran = []
    if a["mode"] == "burn":
        reach = IDX[a["tier"]]  # a job runs when its own window is at least as wide as the current tier
        for j in jobs():
            if j["id"] in done() or IDX[j["tier"]] < reach:
                continue
            ran.append(j["id"])
            if not dry:
                try:
                    r = subprocess.run(shlex.split(j["cmd"]), capture_output=True, text=True, timeout=3600)
                    log(f"job {j['id']} rc={r.returncode}")
                except Exception as e:
                    log(f"job {j['id']} error {e}")
                open(f"{STATE}/done", "a").write(j["id"] + "\n")
                notify(f"nvaex-burn ran {j['id']} ({a['tier']})")
            break  # one job per tick
    a["ran"], a["dry_run"] = ran, dry
    return a


def hook():
    """UserPromptSubmit: stamp activity; under brake, tell Claude to checkpoint. Never blocks."""
    try:
        sys.stdin.read()
    except Exception:
        pass
    os.makedirs(STATE, exist_ok=True)
    open(f"{STATE}/active", "w").write(str(now()))
    a = tick(dry=True)  # evaluate brake only; job dispatch is explicit via `tick`
    if a["mode"] == "brake":
        ctx = f"[nvaex-burn BRAKE] {a['why']}. Stop spawning background work and run /nvaex-burn:sweep to checkpoint. Override: touch ~/.claude/state/off/nvaex-burn"
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": ctx}}))


def keepalive(once):
    lock = f"{STATE}/keepalive.pid"
    os.makedirs(STATE, exist_ok=True)
    if not once:
        try:
            os.kill(int(open(lock).read()), 0)
            print("keepalive already running")
            return
        except (OSError, ValueError):
            open(lock, "w").write(str(os.getpid()))
    while True:
        try:
            idle = now() - float(open(f"{STATE}/active").read())
        except (OSError, ValueError):
            idle = ACTIVE + 1
        if idle > ACTIVE:
            print("session idle; no ping")
            break
        cmd = os.environ.get("BURN_PING_CMD")
        if cmd:
            subprocess.run(shlex.split(cmd), capture_output=True, timeout=60)
        log("keepalive ping" + ("" if cmd else " (log only, BURN_PING_CMD unset)"))
        print("ping")
        if once:
            break
        time.sleep(KEEPALIVE)
    if not once and os.path.exists(lock):
        os.remove(lock)


if __name__ == "__main__":
    c, rest = (sys.argv[1] if len(sys.argv) > 1 else "status"), sys.argv[2:]
    if c == "status":
        print(json.dumps(assess(read_usage())))
    elif c == "tick":
        print(json.dumps(tick("--dry-run" in rest)))
    elif c == "hook":
        hook()
    elif c == "keepalive":
        keepalive("--once" in rest)
    elif c == "notify":
        print("sent" if notify(" ".join(rest)) else "disabled or failed")
    else:
        sys.exit(f"usage: {sys.argv[0]} status|tick|hook|keepalive|notify")
