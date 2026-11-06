---
name: rea-harvest
description: Turn a forked repo into a capability card. Use on /rea-harvest, mining a fork for algorithms or prompts, wrapping a CLI.
---
# rea-harvest (4 stages)

1. **Triage**: `ls`/read the repo README; pick bucket (agent harness, memory/RAG, android/termux, reverse-eng/security, UI).
2. **Deconstruct**: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/harvest.py <repo> --out <dir>`. Always builds the code-review-graph Tree-sitter graph (required; fails if it is missing). Writes `CAPABILITY_CARD.json` (entrypoints, longest functions, prompt files/strings, telemetry hits, packaging gate). The graph is stored in `<dir>/crg-data`, target repo untouched. Optionally map it with the `code-map` skill.
   Then spawn `code-archaeologist` (what is core vs bloat) and `integration-verifier` (does the stripped result still run) in an adversarial loop, max 3 rounds. For a contested keep/strip call use the `rea-review` skill (verified quotes only).
3. **Gate** (card `packaging_gate`; confirm with operator): pure prompt -> write SKILL.md; CLI -> `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/wrap.py <card>` (shim + SKILL.md in `<dir>/wrap`; `--bin-dir ~/.local/bin` installs, ask first); MCP server -> `mcp2cli` skill; daemon/driver -> operator decides.
4. **Registry**: show the card and the line to append to `MANIFEST.jsonl`; do not write it unasked.

Rules: read-only on the target; no network; telemetry files listed in the card are stripped by the human-approved port, never silently.
