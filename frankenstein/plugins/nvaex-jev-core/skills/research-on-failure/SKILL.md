---
name: research-on-failure
description: Use when a command or tool keeps failing or a fix comes from memory. Looks up current dated sources before patching.
---
# Research on failure

Your remembered fix may be stale. Today's date is in the hook note or `date -u`; use it.

1. Name the failure: error class, tool, installed version (read the lockfile or `--version`), OS.
2. List at least 3 candidate fixes, including one upgrade-forward and one minimal stay-put.
3. Search each with the year and version in the query (claw.search or WebSearch). Read official docs, changelogs and the issue tracker first; blogs last. Need two independent current sources per candidate; cite URL and date.
4. Score each: fixes the root cause, official and forward-compatible, not deprecated or EOL, safe, small blast radius, reversible. Prefer the durable fix; label the fast patch as a stop-gap.
5. Stay in the scope of the failing command. No unrelated refactors.
6. Recommend, do not apply, unless asked. If no live source confirms a fix for the installed version, say `insufficient_data`, not a guess.

For high-stakes failures, give each candidate to its own subagent and have one separate verifier try to break the winner.
