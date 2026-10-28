# MEMORY.md — NovAExopia
Durable facts about this repo. Dated; newest first. Updated at session wrap-up.

## 2026-10-28
- **Claw tools live here permanently** (operator): web view, browser tooling, mods. APK repos (AEthX-AEsc, Hyperion-XI) get pre-compiled packages plus marketplace plugins/connectors pointing here.
- **`mcp_connectors/webview/`**: Claude Code plugin wrapping the fork `NvAEx-chrome-devtools-mcp` to drive the phone's own Chrome over the Chrome DevTools Protocol. Android only exposes Chrome's DevTools socket through adb (wireless debugging, loopback); Termux cannot open the abstract socket directly ("Permission denied"). `bin/webview-connect` sets up `adb forward` and checks `/json/version`; `bin/webview-mcp` starts the server and reports link state on stderr. Not tested end to end yet (no device paired; server start blocked by the auto-mode safety classifier).
- **`mods/`**: operator's own mods spec (`cc.do.now.txt`, from Drive `_04.resume.md`) and `SPEC.md`. Mods are built here.

## 2026-10-05
- Created at wrap-up. AGENTS.md is the only instruction file (the old CLAUDE.md content moved there; Claude Code reads AGENTS.md natively).
- `.github/workflows/notify-vault.yml` pings `c10vis-poem/NovAExorpus` when AGENTS.md or RESUME.md change on main, so the vault rebuilds MASTER-AGENTS.md / MASTER-RESUME.md (secret `VAULT_DISPATCH_TOKEN`).
- Runtime memory stack is canonical in aesop-xi (`AGENTS.md` §Runtime memory stack); this repo references it.

## 2026-10-08
- `raw/novaecopia-vincet.md` = condensed version from NovA-Corpus (deleted repo); original in `Merovingian's_keep/_salvage/NovA-Corpus/`.
