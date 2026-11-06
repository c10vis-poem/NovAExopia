import { toMarkdown } from "./md.mjs";
import { run, OPS, select, platformStatus } from "./platform.mjs";
import { listenerStatus } from "./listener.mjs";
import { adbAction } from "./adb.mjs";
import { crawl } from "./crawl.mjs";
import { video } from "./video.mjs";
import { google } from "./google.mjs";
import { ClawError, addSecret } from "./wire.mjs";

const UA = "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/124 Mobile Safari/537.36";
const getText = async (url, init = {}) => { const r = await fetch(url, { ...init, headers: { "User-Agent": UA, ...init.headers }, signal: AbortSignal.timeout(20000) }); return [r, await r.text()]; };

// ---- claw.search: keyless DuckDuckGo HTML endpoint. Override with CLAW_SEARCH_URL (tests, mirrors).
export async function search({ query, limit = 8 }) {
  const url = process.env.CLAW_SEARCH_URL || "https://html.duckduckgo.com/html/";
  const [r, html] = await getText(url, { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: "q=" + encodeURIComponent(query) });
  if (r.status === 202 || r.status === 403 || r.status === 429 || /anomaly|captcha|unusual traffic/i.test(html))
    throw new Error(`search blocked by provider (HTTP ${r.status}, bot check). Retry later or from another network; no results were fabricated.`);
  if (!r.ok) throw new Error(`search provider HTTP ${r.status}`);
  const out = [];
  for (const m of html.matchAll(/<a[^>]+class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>([\s\S]*?)(?=<a[^>]+class="[^"]*result__a|$)/g)) {
    let link = m[1].replace(/&amp;/g, "&"); const u = link.match(/[?&]uddg=([^&]+)/); if (u) link = decodeURIComponent(u[1]);
    const snip = (m[3].match(/class="[^"]*result__snippet[^"]*"[^>]*>([\s\S]*?)<\/(?:a|td|div)>/) || [])[1] || "";
    out.push({ title: toMarkdown(m[2]), url: link, snippet: toMarkdown(snip) });
    if (out.length >= limit) break;
  }
  if (!out.length) throw new Error("search returned no parsable results (provider markup may have changed)");
  return JSON.stringify(out);
}

export async function scrape(a) {
  const { url, action = "fetch", format = "markdown", max_chars = 20000 } = a;
  if (action === "crawl") return crawl(a);
  if (action === "map") return crawl(a, true);
  if (action === "video") return video(a);
  if (action !== "fetch") throw new Error("action must be fetch|crawl|map|video");
  const [r, body] = await getText(url);
  if (!r.ok) throw new Error(`HTTP ${r.status} for ${url}`);
  return (format === "html" ? body : toMarkdown(body)).slice(0, max_chars);
}

// ---- claw.device: platform ops (termux or aesc), built-in adb client, adb binary, rclone (read-only), Google REST.
export async function device(a) {
  const { action, args = [] } = a, s = args.map(String);
  if (action === "platform") return JSON.stringify({ ...platformStatus(), listener: listenerStatus() });
  if (OPS.includes(action)) return select(action).call(action, s);
  if (/^adb-(?:connect|disconnect|shell|tap|install|status)$/.test(action)) return adbAction(action, a);
  if (action === "adb-devices") return run("adb", ["devices"]);
  if (action === "adb") {
    if (!s.length) throw new Error('args: adb arguments, e.g. ["shell","input","tap","10","20"]');
    if (s[0] !== "-s" && !["devices", "connect", "pair", "disconnect", "version", "keygen", "pubkey"].includes(s[0])) {
      const serials = (await run("adb", ["devices"])).split("\n").slice(1).map((l) => l.trim().split(/\s+/)).filter((p) => p[1] === "device").map((p) => p[0]);
      if (serials.length > 1) throw new ClawError(`${serials.length} adb devices attached. Repeat with args ["-s", "<serial>", ...].`, { question: "Which adb device?", options: serials.slice(0, 8) });
    }
    return run("adb", s, 60000);
  }
  if (action === "rclone") { if (!["lsjson", "cat", "lsf", "about", "listremotes"].includes(s[0])) throw new Error("rclone is read-only here: lsjson|cat|lsf|about|listremotes"); return run("rclone", s, 60000); }
  if (action === "google") return google(a);
  throw new Error("action must be one of " + [...OPS, "platform", "adb-connect", "adb-disconnect", "adb-shell", "adb-tap", "adb-install", "adb-status", "adb-devices", "adb", "rclone", "google"].join("|"));
}

// ---- claw.infer: openrouter or gemini via REST, keys from env only.
export async function infer({ provider = "openrouter", model, prompt }) {
  const j = (u, h, b) => fetch(u, { method: "POST", headers: { "Content-Type": "application/json", ...h }, body: JSON.stringify(b), signal: AbortSignal.timeout(120000) }).then(async (r) => { const d = await r.json(); if (!r.ok) throw new Error(`${provider} HTTP ${r.status}: ${JSON.stringify(d).slice(0, 300)}`); return d; });
  if (provider === "openrouter") {
    const k = process.env.OPENROUTER_API_KEY; if (!k) throw new Error("OPENROUTER_API_KEY not set"); addSecret(k);
    return (await j(process.env.CLAW_OPENROUTER_URL || "https://openrouter.ai/api/v1/chat/completions", { Authorization: "Bearer " + k }, { model, messages: [{ role: "user", content: prompt }] })).choices[0].message.content;
  }
  if (provider === "gemini") {
    const k = process.env.GEMINI_API_KEY; if (!k) throw new Error("GEMINI_API_KEY not set"); addSecret(k);
    return (await j(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`, { "x-goog-api-key": k }, { contents: [{ parts: [{ text: prompt }] }] })).candidates[0].content.parts.map((p) => p.text).join("");
  }
  throw new Error("provider must be openrouter|gemini");
}
