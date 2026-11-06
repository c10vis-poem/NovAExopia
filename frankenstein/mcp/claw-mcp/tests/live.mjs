// Real targets over the real network, read-only. Run with CLAW_LIVE=1. No account, no login, no writes.
import { spawn } from "node:child_process";
const [D] = process.argv.slice(2); let bad = 0;
const ck = (n, ok, extra = "") => { console.log(`${ok ? "PASS" : "FAIL"} [real] ${n}${ok ? "" : "  " + String(extra).slice(0, 500)}`); if (!ok) bad = 1; };
const p = spawn("node", [D + "/node/server.mjs"], { env: { ...process.env, CLAW_LISTEN: "off" } });
let buf = "", n = 0; const w = new Map();
p.stdout.on("data", (d) => { buf += d; let i; while ((i = buf.indexOf("\n")) >= 0) { const m = JSON.parse(buf.slice(0, i)); buf = buf.slice(i + 1); w.get(m.id)?.(m); } });
const call = (name, args) => new Promise((res) => { const id = ++n; w.set(id, (m) => res({ err: !!m.result.isError, t: m.result.content[0].text })); p.stdin.write(JSON.stringify({ jsonrpc: "2.0", id, method: "tools/call", params: { name, arguments: args } }) + "\n"); });
const J = (r) => { try { return JSON.parse(r.t.split("\nCHOICE:")[0]); } catch { return {}; } };

let r = await call("claw.search", { query: "Model Context Protocol specification", limit: 3 });
if (r.err && /blocked by provider/.test(r.t)) console.log("BLOCKED [real] search: provider bot check this run: " + r.t.slice(0, 120));
else ck("search returns live results", !r.err && J(r).length > 0 && /^https?:/.test(J(r)[0]?.url), r.t);
r = await call("claw.scrape", { url: "https://www.rfc-editor.org/" }); ck("scrape rfc-editor.org to Markdown (links kept, no tags)", /\[[^\]]+\]\([^)]+\)/.test(r.t) && /RFC/.test(r.t) && !/<body|<div/i.test(r.t), r.t.slice(0, 400));

r = await call("claw.scrape", { action: "crawl", url: "https://www.rfc-editor.org/", max_pages: 3, max_depth: 1, delay_ms: 1000, max_chars: 200, deadline_ms: 60000 });
let j = J(r), origin = "https://www.rfc-editor.org";
ck("crawl real site: bounded and same-origin", !r.err && j.pages?.length >= 1 && j.pages.length <= 3 && j.pages.every((x) => x.url.startsWith(origin)), r.t.slice(0, 400));
console.log(`INFO crawl rfc-editor.org: pages=${j.pages?.length} stopped=${j.stopped} skipped=${JSON.stringify(j.skipped)} ms=${j.elapsed_ms}`);
r = await call("claw.scrape", { action: "map", url: "https://www.rfc-editor.org/", max_pages: 2, max_depth: 1, delay_ms: 1000 }); j = J(r);
ck("map real site: URLs only, stays on origin", !r.err && j.urls?.length === 2 && j.urls.every((x) => x.url.startsWith(origin)) && j.skipped.offsite >= 1 && !r.t.includes('"markdown"'), r.t.slice(0, 300));

// Video: a stable, public video with captions.
for (const [label, url] of [["YouTube", "https://www.youtube.com/watch?v=jNQXAC9IVRw"]]) {
  r = await call("claw.scrape", { action: "video", url, max_chars: 400 }); j = J(r);
  console.log(`INFO video ${label}: err=${r.err} via=${j.via} title=${JSON.stringify(j.metadata?.title)} duration=${j.metadata?.duration} transcript=${j.transcript ? j.transcript.lang + "/" + j.transcript.kind + "/" + j.transcript.cues + " cues" : "null"} notes=${JSON.stringify(j.notes || [])}`);
  if (j.transcript) console.log("INFO transcript head: " + j.transcript.text.slice(0, 120).replace(/\n/g, " / "));
  if (r.err) console.log("INFO video error: " + r.t.slice(0, 300));
  ck(`video ${label}: real metadata`, !r.err && !!j.metadata?.title, r.t.slice(0, 400));
  ck(`video ${label}: real transcript`, !!j.transcript?.text, r.t.slice(0, 400));
}
p.stdin.end();
process.exit(bad);
