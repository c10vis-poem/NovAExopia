# SOURCES

## Copied
| path here | origin | version | license |
|---|---|---|---|
| bin/webview-connect | `NovAExopia` worktree `mcp_connectors/webview/bin/webview-connect` (own repo) | 2026-11-04 | repo license |
| bin/killswitch.sh | `frankenstein/shared/killswitch.sh` | - | repo license |
| licenses/LICENSE.chrome-devtools-mcp | `~/repos/NvAEx-chrome-devtools-mcp/LICENSE` | Apache-2.0 | Apache-2.0 |
| licenses/LICENSE.playwright-mcp | `~/repos/playwright-mcp/LICENSE` | Apache-2.0 | Apache-2.0 |

## Distilled (read, rewritten short; no code copied)
| here | from | before | after |
|---|---|---|---|
| skills/browser-cdp | NvAEx-chrome-devtools-mcp `skills/chrome-devtools`, `docs/debugging-android.md`; playwright-mcp snapshot/wait pattern | skills+docs 262KB, playwright-mcp 629KB | 1.3KB |
| skills/android-adb | adb-mcp idea (plugin is only `.mcp.json`), AEthX-AEsc `adb_loopback/POINTER.md` | 87KB plugin | 1.4KB |
| skills/google-access | google-multi-account 0.7.0 (`~/.claude/plugins/synced/a5d13a90.../ba923796...`) design | 296KB | 1.3KB |
| skills/gemini-genai | consensus idea | 128KB | 0.9KB |

## Brought in from `~/.claude/skills` (own work, 2026-11-05), cleaned for a public repo
| here | what was stripped |
|---|---|
| skills/android-termux-operator (SKILL.md, references/audio-pipeline.md) | device make and model; personal tablet and desktop layout; references to private tools and scripts (ccv, vv, speakd, speak, ~/bin, ~/models); ECC mentions; observation numbers; session anecdotes and dates; the operator's stated preferences. audio-pipeline.md was rewritten from 9.2KB to 4.2KB, keeping only Termux facts |
| skills/termux-helper | private paths (~/.claude/NPU-ON-DEVICE.md, ~/tools/geniex-bench, vault and Documents paths, a model file path); the operator's Qwen model rule; the "Where This Lives" part; private project name in the port table. Kept: Aesop-Xi references, that repo is public |

The two `~/.claude/skills` copies are unchanged and now differ from these. No secrets were found in either source. `tests/selftest.sh` fails if private path shapes come back.

## Written new
`node/{server,cdp,drivers,md,wire,platform,listener,adb,crawl,video,google}.mjs` (Node built-ins only: fetch, WebSocket, child_process, net, tls, crypto), `tests/{selftest.sh,check.mjs,check2.mjs,live.mjs,fake-cdp.mjs,fake-adbd.mjs,fake-services.mjs}`, `bin/claw-mcp`, `workflows.json`, `kotlin/**` (kept as the later APK form; untested).

## Size
Package before this fold: 22,900 bytes of files (99KB on disk). After: ~73KB of files (188KB on disk, of which licenses 22KB): grew because search, scrape-to-Markdown, CDP actions and device/Google/rclone drivers are now real. Removed: `python/claw_mcp.py` (5.2KB, replaced by the Node server per FOLD-BRIEF).

## Finish pass 2026-11-05: what informed the new code
No code copied. `node/adb.mjs` is written from the public ADB wire protocol; no adb source is on the phone in this package and none was vendored. Its key format was checked against the real `adb keygen`. `node/video.mjs` drives the installed `yt-dlp`; the caption-first idea is from `~/repos/C10vis-claude-video` `skills/watch/SKILL.md` (read, not copied). `node/google.mjs` extends this package's earlier code. CHOICE form from `plugins/nvaex-ui-cockpit/hooks/lib/cards.ts` (read only; not imported at runtime).

## FOLD-MAP rows homed here (8)
| row | result |
|---|---|
| claude-bridge | folded: claw.browser CDP actions replace it |
| playwright | folded (parts): snapshot via AX tree, wait, selector click/type, as claw.browser + skills/browser-cdp. No server, no bundled browser |
| TinyFish | partly: claw.search + claw.scrape + claw.browser cover search/fetch/browse. NOT folded: hosted run_web_automation, deep research, monitors, datasets, profile vault |
| firecrawl | folded (no hosted parts): scrape to Markdown, crawl, map. No JS rendering in crawl |
| adb-mcp | partly: Termux:API, raw `adb` passthrough, built-in client (connect/shell/tap/install, STLS and AUTH handshakes). NOT folded: test/build helpers, the AF_UNIX + SCM_RIGHTS handshake, `adb forward` in the built-in client. Built-in client proven only against a fake; no real adbd yet |
| consensus | partly: claw.infer openrouter+gemini, two-call pattern in skills/gemini-genai. No hook, no automatic multi-model run |
| apify | partly: bulk driver is claw.scrape crawl/map. NOT folded: actor runner, hosted runs |
| watch-video | partly: claw.scrape action=video gives metadata and caption transcripts, live-proven on one YouTube video. NOT folded: frames, Whisper for videos with no captions, Gemini video |

## Brief scope additions
Chrome DevTools toolkit: folded as claw.browser + skill. Playwright skills: folded as skill. Google API/MCP: folded as `claw.device action=google` (read, plus confirm-gated Drive create, Gmail draft, Calendar create; no send, delete or share) + rclone read-only. Proven only against a fake: no credentials, real Google untested. No OAuth flow built. Android: partly (above). Custom Tabs: not drivable, stated in skills/browser-cdp. GenAI toolkit: gemini via REST only.

## Missing (not on the phone, not invented)
**AEsopXi-mobile-harness** (c10vis-poem fork of droidrun/mobile-harness, synced at 321868e, MIT): it is Markdown only. `skills/phone-control` trims its Android guide, recovery and credential guides; `skills/phone-control/cards/` copies the Chrome, Settings and Gmail cards. Not taken: the `mobilerun_core` Python client and Portal app (claw.device and the built-in ADB client do this job), iOS, cloud, the eBay card, the memory guide (nvaex-memory owns memory).

Goodbye-Termux-ADB, claude-android-skill, `Merovin-genai-for-developers-`, `NxAEx-gemini-skills` (find over ~/repos, ~/.claude/plugins, ~/local-plugins). Spec's "Device and browser toolkit architecture proposal.md" not read; tool arguments are my minimal design.
