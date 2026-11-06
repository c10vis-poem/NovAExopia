---
name: browser-cdp
description: "Drive the phone's Chrome via claw.browser (CDP): read pages, click, type, snapshots, logged-in sites."
---
Distilled from chrome-devtools-mcp (`skills/chrome-devtools`, `docs/debugging-android.md`) and playwright-mcp (snapshot-first, wait-before-act). No server or bundled browser.

Link: `sh bin/webview-connect` (= `adb forward tcp:9222 localabstract:chrome_devtools_remote`), Chrome open on the phone.

Loop: `open`/`navigate` -> `wait` (selector you expect) -> `read format=snapshot` (roles + names, cheap) or `read` (Markdown) -> `click`/`type` by CSS selector -> `read` again. Take a fresh read after any page change; selectors go stale.

Rules:
- Prefer `snapshot` over `html`; `max_chars` caps output.
- `eval` for data the read misses; `cdp` (method, params) for anything else, e.g. `Page.captureScreenshot`, `Network.enable`.
- Logged-in sites: the operator signs in by hand in their own Chrome; drive that tab. The tool refuses password fields and never stores credentials or cookies.
- Custom Tabs: not drivable (they hold no DevTools socket). `device open-url` opens a URL in the default browser; use `claw.browser open` when you need control.
- `CHOICE:` in a result means the operator must pick: which tab (then pass `tab=`), which match of a selector (then pass `index=`), or sign in by hand.
- Bulk reading without a browser: `claw.scrape action=crawl|map`. Video transcripts: `claw.scrape action=video`.
- Not tested against a real phone Chrome (no adb device paired); tested against a fake CDP server.
