# claw-mcp

One MCP server for device, browser, scrape, search and inference I/O: `claw.search`, `claw.scrape`, `claw.browser`, `claw.device`, `claw.infer`, `claw.workflows` (blueprint 4B, server 1). stdio only, plus one local socket for the Aesc daemon.

Node.js stdio server (`node/`, built-ins only, Node 22+; phone has v26). `kotlin/` is the later APK-embedded form, **untested** (JDK 21 present, gradle not), and does not have this pass's additions.

| tool | does |
|---|---|
| `claw.search` | keyless DuckDuckGo HTML provider; JSON results; clear error if the provider blocks |
| `claw.scrape` | `action=fetch` (default) URL to Markdown, `format=html` for raw. `crawl`/`map`: bulk, see below. `video`: metadata + transcript, see below |
| `claw.browser` | Chrome over CDP at 127.0.0.1:9222: version, tabs, open, close, navigate, read (markdown/html/snapshot), eval, wait, click, type, cdp. Refuses password fields |
| `claw.device` | platform ops (termux or aesc backend), built-in ADB client, `adb` argv, read-only `rclone`, Google Drive/Gmail/Calendar REST per account |
| `claw.infer` | openrouter or gemini (keys from env) |
| `claw.workflows` | named tool sequences from `workflows.json`; a CHOICE pauses the sequence |

Skills in `skills/`: browser-cdp, android-adb, google-access, gemini-genai, phone-control, termux-helper, android-termux-operator (with `references/audio-pipeline.md`).

Logged-in sites: sign in yourself in the phone's Chrome; claw drives that tab and never handles passwords.

## Platform layer (`node/platform.mjs`)
One interface, `{name, available(), has(op), call(op, args)}`, two backends, chosen at runtime per call. `termux` runs Termux:API binaries. `aesc` forwards to the Aesc daemon once it has connected and registered its ops. Default prefers aesc for the ops it registered, then termux; if the daemon disconnects, the next call falls back. `CLAW_PLATFORM=termux|aesc` forces one, and then there is no silent fallback. `claw.device action=platform` shows who serves what. Outside tools (adb, rclone, yt-dlp, getprop) go the same way: Aesc registers `exec:<tool>` and serves `device/exec {cmd, args, ms}`. Search, scrape, crawl and browser are plain network calls from the server, so they need no backend. The server itself still needs a Node runtime, which Aesc must supply, or the Kotlin form must catch up (`kotlin/` has none of the newer tools).

## Socket for the Aesc daemon (`node/listener.mjs`)
Lives and dies with the stdio server; nothing stays running. Newline-delimited JSON-RPC 2.0, both directions on one connection.

- `CLAW_LISTEN`: `unix:<path>` (default `~/.claude/state/claw-mcp/claw.sock`, mode 0600), `tcp:127.0.0.1:PORT` (loopback only, anything else is refused), or `off`.
- TCP needs `auth {token}` first: `CLAW_LISTEN_TOKEN`, else a generated `claw.token` (0600) in the state dir. Aesc is a separate APK with its own Android user, so it cannot open a 0600 Termux socket: **use TCP with `CLAW_LISTEN_TOKEN` for that case** (design reasoning, not yet tried with a real Aesc).
- Client to claw: `initialize`, `ping`, `tools/list`, `tools/call`, `aesc/register {name, ops}`. Claw to client after registering: `device/call {op, args}`.
- A second claw on the same path leaves the live socket alone and runs without a listener. So with several sessions open, the first one owns the socket.

## CHOICE lines
When a step needs an operator pick, the result ends with `CHOICE: question | a | b`, the form `nvaex-ui-cockpit` `hooks/lib/cards.ts` parses. Raised for: several Chrome tabs and none selected; a selector matching several elements; a password field (sign in by hand); Chrome or ADB unreachable; the phone's debugging prompt unanswered; several adb devices; several Google accounts; a video with no English captions; a Google write without `confirm=true`. An option's text works as the answer (`tab=<option>`).

Page text is defused: cards.ts scans the whole result, so a web page printing `CHOICE: ...` or `{"choice":{...}}` could otherwise raise a card. Claw puts U+200B into any such text it returns, so only claw's own line can match.

## Built-in ADB client (`node/adb.mjs`)
Speaks the adbd wire protocol directly over a loopback socket. No adb binary, Shizuku or Tasker. **Pairing stays with the operator**: `adb pair` puts `~/.android/adbkey` (`CLAW_ADB_KEY`) on the phone's trusted list and this client reuses that key; the key is never printed.

- Actions: `adb-connect` (`port`, `host`), `adb-shell` (`command`; returns stdout, stderr, exit), `adb-tap` (`x`, `y`), `adb-install` (`path`, streamed with `cmd package install -S`, Android 7+), `adb-status`, `adb-disconnect`.
- Both adbd modes: wireless debugging (A_STLS, then TLS 1.3 with a client certificate over the adb key) and classic `adb tcpip` (A_AUTH signature, then public key, which shows the phone's prompt).
- Port: `port`, then `CLAW_ADB_PORT`, then `getprop service.adb.tls.port` / `service.adb.tcp.port`, then 5555. Those properties were empty when probed (wireless debugging may simply have been off), so give the port from the Wireless debugging screen if discovery fails. mDNS discovery is not implemented.
- Not here: `adb forward`. CDP still uses `bin/webview-connect`, which needs the adb binary.

## Bulk crawl (`claw.scrape action=crawl|map`, `node/crawl.mjs`)
Same-origin unless `same_origin=false`. One request at a time. `max_pages` 10 (cap 200), `max_depth` 2 (cap 5), `delay_ms` 1000 (floor 250, measured from the end of the last response), `deadline_ms` 120 s (cap 300 s), 2 MB per page, 20 MB total. Honours robots.txt and Crawl-delay; `respect_robots=false` opts out. Stops at the first HTTP 429/503 and reports Retry-After. Offsite redirects are not followed. Identifies itself as `claw-mcp`. `same_origin=false` still skips private addresses by hostname text (no DNS check) unless the crawl started on one. No JS rendering: use `claw.browser` for those pages.

## Video (`claw.scrape action=video`, `node/video.mjs`)
Uses `yt-dlp` (already on the phone; `CLAW_YTDLP` overrides). Without it, or when it fails, it reads the page: YouTube player JSON, or `og:` tags and `<track>` on any page. Args: `lang`, `timestamps`, `metadata_only`, `max_chars`. **No captions means no transcript**: `transcript: null` and a note saying why. Speech-to-text and video frames are not here.

## Google (`claw.device action=google`, `node/google.mjs`)
Local REST route for Drive, Gmail and Calendar. One file per account, `$CLAW_GOOGLE_DIR/google-<account>.json` (default `~/.config/claw-mcp`), mode 0600 or it is refused: `{client_id, client_secret, refresh_token}`, or `{access_token, expiry}`.

| service | ops |
|---|---|
| drive | list (`query`), get, read (Docs/Sheets/Slides exported as text; binaries not printed), create |
| gmail | list (`query`), get, thread, labels, draft |
| calendar | list (`query`, `time_min`, `time_max`, `calendar`), get, calendars, create |

Writes are only Drive create, Gmail draft and Calendar create (no invitations), and each needs `confirm=true`. **Nothing sends mail, deletes or shares**, so the claude.ai connectors still cover those. All server output, errors included, passes through a redactor that knows every value read from a token file. `CLAW_GOOGLE_BASE` (tests) accepts only `http://127.0.0.1`, so an env var cannot send tokens elsewhere.

Getting the token files is not done here and no OAuth flow is built: it needs an OAuth client and the operator's consent for each account.

## Swap in / out
Add to a repo's `.mcp.json` (swap out = delete the entry or `claude mcp remove claw`):
```json
{"mcpServers":{"claw":{"command":"sh","args":["<path-to>/frankenstein/mcp/claw-mcp/bin/claw-mcp"]}}}
```
(`sh`, not the script directly: Termux has no `/usr/bin/env`.) Per-repo scope via `.claude/harness-scope.json` (AEthX-AEsc loads claw-mcp).

## Hooks and kill switches
Hooks registered: none. The server itself honours the kill switch at start: `touch ~/.claude/state/off/claw-mcp` (or `claw-mcp.server`, or `~/.nvaex-hooks-off`) and it exits 0 offering no tools; remove the file to restore.

## Env
`CDP_PORT` (9222), `OPENROUTER_API_KEY`, `GEMINI_API_KEY`, `CLAW_SEARCH_URL`, `CLAW_WORKFLOWS` (path to workflows JSON: `{"name":[{"tool":"claw.device","arguments":{...}}]}`), `CLAW_PLATFORM`, `CLAW_LISTEN`, `CLAW_LISTEN_TOKEN`, `CLAW_STATE_DIR`, `CLAW_ADB_KEY`, `CLAW_ADB_PORT`, `CLAW_ADB_AUTH_WAIT`, `CLAW_YTDLP`, `CLAW_GOOGLE_DIR`, `CLAW_GOOGLE_BASE`. `bin/webview-connect` brings up the adb forward to Chrome (see mcp_connectors/webview).

## Tested on device
`CLAW_LIVE=1 sh tests/selftest.sh` (Termux arm64, 2026-11-05): 166 checks, 0 failed. Each line of the new suite says what proved it. **A fake is not proof that the real thing accepts this code.**

- **Against the real thing (32 checks):** live DuckDuckGo search; live scrape, crawl and map of rfc-editor.org; a live YouTube video through yt-dlp (metadata and captions); Termux:API battery; unix and TCP sockets, permissions and cleanup, including SIGKILL and SIGTERM; adb public key encoding matched against the real `adb keygen`; the TLS certificate accepted by the real `openssl`; adb errors on refused and non-adb ports.
- **Only against a fake (108 checks, plus 26 older browser, search and infer checks on `tests/fake-cdp.mjs`):** every ADB session step (`tests/fake-adbd.mjs`), CDP browser actions, the Aesc peer, every Google call (`tests/fake-services.mjs`), crawl edge cases, video edge cases with a stub yt-dlp. CHOICE lines were checked once with the real `cards.ts` (`CLAW_CARDS_TS=<path>`); by default the selftest uses a mirror of it, to stay self-contained.
- **Untested:** a real adbd (no paired device: port 5555 refused, `adb devices` empty) so connect, shell, install and tap have never touched a phone; real phone Chrome; a real Aesc daemon (none exists yet); real Google APIs (no credentials); the cockpit actually drawing a card from a live claw result.

The selftest leaves nothing running: fakes die with it, the adb binary is stubbed so no adb server starts, and state goes in a temp dir. Tail:
```
INFO video YouTube: err=false via=yt-dlp title="Me at the zoo" duration=19 transcript=en/captions/6 cues notes=[]
INFO transcript head: [0:01] All right, so here we are, in front of the elephants / [0:05] the cool thing about these guys is that they have rea
PASS [real] video YouTube: real metadata
PASS [real] video YouTube: real transcript
UNTESTED real adbd (phone not paired; the client has only met tests/fake-adbd.mjs)
UNTESTED real phone Chrome over CDP (only tests/fake-cdp.mjs)
UNTESTED real Aesc daemon (only a fake peer on the real socket)
UNTESTED real Google APIs (no credentials; only tests/fake-services.mjs)
SELFTEST PASS
```

## Install
```
/plugin install claw-mcp --marketplace c10vis-poem/NovAExopia
```
On this phone before it ships: `claude plugin marketplace add ~/repos/.wt/novaexopia-frankenstein2` then `claude plugin install claw-mcp@novaexopia`. Swap out: `claude plugin disable claw-mcp@novaexopia`.
