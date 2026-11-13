"""Every hook of every plugin, run with three bad inputs, must exit 0 with nothing for the owner's screen (no stderr,
no systemMessage). Contract A3 3d (2026-11-12).
  hooks_quiet.py              the source copies: NovAExopia plugins/, the vault's greedy-crane, the rules-plugin worktree
  hooks_quiet.py --installed  the copies Claude Code runs (~/.claude/plugins/installed_plugins.json)
Writes docs/audits/2026-11-12/hooks-quiet.txt; first line ALL QUIET, or one FAIL line per hook and input."""
import concurrent.futures
import json
import os
import subprocess
import sys
import tempfile

HOME = os.path.expanduser("~")
REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
OUT = os.path.join(REPO, "docs", "audits", "2026-11-12", "hooks-quiet.txt")
SOURCES = [os.path.join(REPO, "plugins", n) for n in sorted(os.listdir(os.path.join(REPO, "plugins")))] + [
    "/storage/emulated/0/Documents/NovAExorpus/plugins/greedy-crane",
    os.path.join(HOME, "repos", "wt", "a3-aesop-xi", "plugins", "aesops-enforcements")]
INPUTS = {"empty": "", "not-json": "this is not json", "no-key": "{}"}


def plugin_roots(installed):
    if not installed:
        return [p for p in SOURCES if os.path.isdir(p)]
    with open(os.path.join(HOME, ".claude", "plugins", "installed_plugins.json")) as f:
        d = json.load(f).get("plugins", {})
    return sorted({e["installPath"] for v in d.values() for e in v if os.path.isdir(e.get("installPath", ""))})


def hook_commands(root):
    out = []
    for hj in (os.path.join(root, "hooks", "hooks.json"), os.path.join(root, "hooks.json")):
        try:
            with open(hj) as f:
                hooks = json.load(f).get("hooks", {})
        except (OSError, ValueError):
            continue
        if not isinstance(hooks, dict):
            continue
        for event, entries in hooks.items():
            for e in entries if isinstance(entries, list) else []:
                for h in e.get("hooks", []) if isinstance(e, dict) else []:
                    if h.get("type") == "command" and h.get("command"):
                        out.append((event, h["command"], h.get("args"), h.get("timeout") or 20, hj))
        break  # hooks/hooks.json is the Claude one; a root hooks.json beside it belongs to another agent
    return out


def run_one(root, event, command, args, timeout, inp_name, inp):
    home = tempfile.mkdtemp(prefix="hq-")
    env = {"HOME": home, "PATH": os.environ.get("PATH", ""), "CLAUDE_PLUGIN_ROOT": root,
           "LANG": os.environ.get("LANG", "C.UTF-8"), "PREFIX": os.environ.get("PREFIX", ""), "TMPDIR": home}
    sub = lambda s: s.replace("${CLAUDE_PLUGIN_ROOT}", root)
    argv = [sub(command)] + [sub(a) for a in args] if args else ["sh", "-c", sub(command)]
    try:
        r = subprocess.run(argv, input=inp, capture_output=True, text=True, timeout=timeout, env=env, cwd=home)
    except subprocess.TimeoutExpired:
        return f"FAIL {root} {event} [{inp_name}]: timed out after {timeout}s"
    except OSError as e:
        return f"FAIL {root} {event} [{inp_name}]: could not start ({e.strerror})"
    bad = []
    if r.returncode != 0:
        bad.append(f"exit {r.returncode}")
    if r.stderr.strip():
        bad.append("stderr: " + r.stderr.strip().splitlines()[-1][:160])
    if '"systemMessage"' in r.stdout:
        bad.append("systemMessage on the owner's screen")
    return f"FAIL {root} {event} [{inp_name}]: " + "; ".join(bad) if bad else None


def main():
    installed = "--installed" in sys.argv
    jobs = [(root, *h[:4], n, i) for root in plugin_roots(installed) for h in hook_commands(root) for n, i in INPUTS.items()]
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        res = list(ex.map(lambda j: run_one(*j), jobs))
    fails = [r for r in res if r]
    head = "ALL QUIET" if not fails else f"{len(fails)} FAIL"
    lines = [f"{head} ({'installed' if installed else 'source'} copies: {len(jobs)} runs, "
             f"{len({j[0] for j in jobs})} plugins)"] + fails
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT if not installed else OUT.replace(".txt", "-installed.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
