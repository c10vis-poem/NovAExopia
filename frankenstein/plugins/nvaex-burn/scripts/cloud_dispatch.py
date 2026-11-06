#!/usr/bin/env python3
"""cloud_dispatch: write a job file for cloud work. POSTs it only if AG_BRIDGE_URL is set AND send is true. Stdlib only.
Input on stdin: JSON {job, payload?, target?, send?}. Prints a JSON result. Called by the ag.cloud_dispatch tool (mcp/burn-mcp).
Env: AG_JOBS_DIR (default <BURN_STATE>/jobs, BURN_STATE default ~/.claude/state/nvaex-burn), AG_BRIDGE_URL (unset = never contacts cloud)."""
import json, os, sys, time, urllib.request, uuid

STATE = os.environ.get("BURN_STATE") or os.path.expanduser("~/.claude/state/nvaex-burn")
JOBS = os.environ.get("AG_JOBS_DIR") or os.path.join(STATE, "jobs")
BRIDGE = os.environ.get("AG_BRIDGE_URL", "")


def dispatch(job, payload, target, send):
    os.makedirs(JOBS, exist_ok=True)
    jid = time.strftime("%Y%m%dT%H%M%S-") + uuid.uuid4().hex[:6]
    rec = {"id": jid, "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "job": job,
           "target": target or "antigravity", "payload": payload, "sent": False}
    p = os.path.join(JOBS, jid + ".json")
    with open(p, "w") as f: json.dump(rec, f, indent=1)
    res = {"job_file": p, "sent": False, "bridge_configured": bool(BRIDGE)}
    if send and BRIDGE:
        try:
            rq = urllib.request.Request(BRIDGE, json.dumps(rec).encode(), {"Content-Type": "application/json"})
            with urllib.request.urlopen(rq, timeout=15) as r: res.update(sent=True, http=r.status)
        except Exception as e:
            res["send_error"] = str(e)
    elif send:
        res["note"] = "send requested but AG_BRIDGE_URL not set; job file only"
    return res


if __name__ == "__main__":
    a = json.load(sys.stdin)
    if not a.get("job"): sys.exit("job is required")
    print(json.dumps(dispatch(a["job"], a.get("payload"), a.get("target"), bool(a.get("send")))))
