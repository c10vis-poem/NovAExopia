#!/usr/bin/env python3
"""agent-configs-panel backend, read-only. Tab-separated: kind, name, state, detail.
  agentconfigs.py items [--repo DIR]   market/pkg/wf rows
Marketplaces from known_marketplaces.json; packages = installed plugins with their agents; workflows = harness-scope profiles."""
import json, os, sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
from inventory import CL, load  # noqa: E402
import profiles  # noqa: E402


def main(a):
    repo = a[a.index("--repo") + 1] if "--repo" in a else os.getcwd()
    for name, m in load(CL / "plugins" / "known_marketplaces.json").items():
        s = m.get("source", {})
        where = s.get("repo") or s.get("path") or s.get("url") or s.get("source", "")
        mf = load(Path(m.get("installLocation", "")) / ".claude-plugin" / "marketplace.json")
        print(f"market\t{name}\t{len(mf.get('plugins', []))} plugins\t{where}")
    en = load(CL / "settings.json").get("enabledPlugins", {})
    for key, es in load(CL / "plugins" / "installed_plugins.json").get("plugins", {}).items():
        root = Path((es[0] if es else {}).get("installPath", ""))
        ags = sorted(f.stem for f in root.glob("agents/*.md")) if root.is_dir() else []
        if ags or key.startswith("nvaex-"):
            print(f"pkg\t{key}\t{'on' if en.get(key) else 'off'}\t{', '.join(ags) or 'no agents'}")
    cur = profiles.current(repo)
    for n in profiles.profiles():
        print(f"wf\t{n}\t{'on' if n == cur else 'off'}\tharness-scope profile")


if __name__ == "__main__":
    main(sys.argv[1:])
