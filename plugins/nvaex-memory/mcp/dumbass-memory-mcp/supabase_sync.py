#!/usr/bin/env python3
"""Mirror the vault's observation JSONL into Supabase (tables from vault supabase/migrations/20261113150000_memory.sql).

What it solves: git carries memory to every device, but a database answers queries (full-text, vectors) from anywhere.
This pushes every JSONL record into public.mem_observations and its sha256 into public.mem_cas, upserting by id, so
re-running is safe. Stdlib only. Keys come from nvaex-secret (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY) or the
environment; they are never printed.
Run: python3 supabase_sync.py [--project NAME]
"""
import json, os, subprocess, sys, urllib.request, urllib.error
import observations as O

SECRET_CLI = os.path.expanduser("~/bin/nvaex-secret")


def secret(name):
    v = os.environ.get(name, "").strip()
    if v:
        return v
    r = subprocess.run([SECRET_CLI, "get", name], capture_output=True, text=True, timeout=30)
    if r.returncode != 0 or not r.stdout.strip():
        raise SystemExit("missing %s (nvaex-secret set %s)" % (name, name))
    return r.stdout.strip()


def post(url, key, table, rows):
    req = urllib.request.Request(
        "%s/rest/v1/%s?on_conflict=%s" % (url, table, "id" if table == "mem_observations" else "sha256"),
        data=json.dumps(rows).encode(), method="POST",
        headers={"apikey": key, "Authorization": "Bearer " + key, "Content-Type": "application/json",
                 "Prefer": "resolution=merge-duplicates,return=minimal"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return "%d %s" % (e.code, e.read(300).decode("utf-8", "replace"))


def rows(project=None):
    out = []
    for name in sorted(os.listdir(O.SHARED)) if os.path.isdir(O.SHARED) else []:
        if not name.endswith(".jsonl"):
            continue
        for line in open(os.path.join(O.SHARED, name), encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if project and r.get("project") != project:
                continue
            out.append(r)
    return out


def main():
    project = sys.argv[sys.argv.index("--project") + 1] if "--project" in sys.argv else None
    url, key = secret("SUPABASE_URL").rstrip("/"), secret("SUPABASE_SERVICE_ROLE_KEY")
    recs = rows(project)
    obs = [{"id": r["id"], "kind": r.get("kind", "observation"), "project": r["project"], "session": r.get("session"),
            "type": r.get("type"), "created_at": r["created_at"], "title": r.get("title"), "subtitle": r.get("subtitle"),
            "narrative": r.get("narrative") or "\n".join("%s: %s" % (k, r[k]) for k in O.SUM_FIELDS if r.get(k)) or None,
            "text": r.get("text"), "facts": O.as_list(r.get("facts")), "concepts": O.as_list(r.get("concepts")),
            "files": O.as_list(r.get("files") or (r.get("files_read", []) + r.get("files_edited", []))),
            "source": r.get("source"), "raw": r} for r in recs]
    cas = [{"sha256": r["id"], "label": "observation:%s" % r["project"], "repo": r["project"],
            "bytes": len(json.dumps(r))} for r in recs]
    a = post(url, key, "mem_observations", obs) if obs else "nothing"
    b = post(url, key, "mem_cas", cas) if cas else "nothing"
    print(json.dumps({"records": len(recs), "mem_observations": a, "mem_cas": b}))
    sys.exit(0 if a in (200, 201, "nothing") and b in (200, 201, "nothing") else 1)


if __name__ == "__main__":
    main()
