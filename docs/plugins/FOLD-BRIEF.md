# Fold brief, 2026-11-05 (operator's orders for the rebuild)

Goal: **no stock plugin runs as-is.** Every keep is stripped down and folded into a custom package here. All stock plugins then get removed from both claude.ai accounts and turned off on devices. Everything lives in this repo, so it is persistent and not tied to one phone or session.

## Whole ports (the only ones allowed as-is)
`task-observer`, `code-review-graph`. Nothing else, unless the operator names it.

## The keep list
Source: `~/.claude/session-work/2026-11-05/rebuild/keep-list-2026-10-30.md` section 1 (119 keeps), with these operator changes since:
- **Removed (do not fold):** claude-code-cost, claude-code-feedback, pmm, all shipwrights, The Pragmatic PM Toolkit, thinking-partner, token-saver, Token Inspector, claude-war-room (operator disabled it), and every plugin whose job is displaying usage (heavy-usage, cache-ttl-timer, burn-baby-burn, cache-guard, usage bars): the operator is building a custom usage display. nvaex-burn's scope is unchanged unless the mapper finds a conflict: report it.
- **Added keeps:** Memory Bank, mindmap-skills, Prompt Enhancer, claude-time, agent-smith, local-whisper, create-smartfolder, google-multi-account.
- **Rip apart and trim, never whole:** superpowers (verification-before-completion, writing-plans, systematic-debugging; no "MUST invoke" hook), Playwright (parts only, for the Hyperion WebView interceptor and claw.browser).
- **Replaced by claw-mcp:** TinyFish, firecrawl, apify, claude-bridge, watch-video, adb-mcp, playwright as a server (blueprint 4B.1).

## Rules
- `docs/plugins/CONTRACT.md` binds everything. No commits, pushes or installs.
- Every keep gets exactly one home, or a stated reason it can't be folded yet. Nothing silently dropped.
- Trim for real: record before/after size per source in `SOURCES.md`.
- A test that only proves a stub answers is a failure, not a pass. Not-implemented is reported as not implemented.

## claw-mcp scope additions (operator, 2026-11-05 11:27)
claw-mcp is the operator's own browser and web toolkit. Besides search/scrape/CDP it must carry, as drivers or as a trimmed skill set in the package:
- **Chrome DevTools toolkit:** strip `~/repos/NvAEx-chrome-devtools-mcp` for its tool list and CDP patterns.
- **Playwright skills:** the useful parts from `~/repos/playwright-mcp` and `~/repos/playwright` (snapshot/accessibility tree, wait logic, selectors); no server, no bundled browsers.
- **Google API + Google MCP:** Drive/Docs/Gmail/Calendar access for BOTH accounts, reusing the `google-multi-account` plugin's design (note: its MCP fails here with ENOENT, find why) and rclone remotes; tokens never in the repo.
- **Android:** Android MCP / adb patterns from `Goodbye-Termux-ADB`, `claude-android-skill`, `adb-mcp`, and `AEthX-AEsc/adb_loopback/POINTER.md` (ADB loopback: 127.0.0.1:5555, AF_UNIX + SCM_RIGHTS handshake).
- **GenAI toolkit:** fork `c10vis-poem/Merovin-genai-for-developers-` (clone read-only under `~/repos/.review/`), plus `NxAEx-gemini-skills`: trimmed skills for calling Gemini/Vertex.
- **Custom Tabs + WebSockets:** Chromium Custom Tabs control and raw WebSocket/CDP frames (runbook Tier 5: `claw.custom_tab_open`, `claw.cdp_tabs`, `claw.scrape_markdown`).
Keep the blueprint's 6 tools (`claw.search/scrape/browser/device/infer/workflows`) as the MCP surface: these are sub-actions and skills behind them, not more tools. Anything not working on the device is reported as not working.

## claw-mcp language (operator, 2026-11-05 11:28): OVERRIDES any task text saying python/claw_mcp.py
Build claw-mcp as a **local Node.js stdio MCP server** in `mcp/claw-mcp/node/` (Node built-ins: fetch, WebSocket; no heavy deps), reusing the Node code in `NvAEx-chrome-devtools-mcp` and `playwright-mcp`. `bin/claw-mcp` launches it. The Python shim is removed once the Node server passes. The Kotlin source stays as the later APK-embedded form. Runs on the device, never on Cloudflare: it has to reach the phone's Chrome, ADB and Termux:API.
