// claw.scrape action=crawl|map: bounded, polite, same-origin by default. Sequential, honours robots.txt and Crawl-delay,
// stops on HTTP 429/503, and identifies itself rather than posing as a browser.
import { toMarkdown } from "./md.mjs";

const UA = "claw-mcp/0.3 (local operator tool)", ROBOTS_AGENT = "claw-mcp";
const LIMITS = { max_pages: [10, 200], max_depth: [2, 5], deadline_ms: [120000, 300000] };
const MIN_DELAY = 250, DEFAULT_DELAY = 1000, MAX_ROBOTS_DELAY = 10000, PAGE_BYTES = 2 * 1024 * 1024, TOTAL_BYTES = 20 * 1024 * 1024, OUTPUT_CHARS = 200000;
const SKIP_EXT = /\.(?:png|jpe?g|gif|webp|svg|ico|css|js|mjs|map|woff2?|ttf|eot|pdf|zip|gz|tgz|bz2|xz|7z|rar|tar|apk|exe|dmg|iso|mp[34]|m4[av]|webm|mkv|avi|mov|wav|ogg|flac)$/i;
const PRIVATE = /^(?:localhost$|127\.|10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.|169\.254\.|0\.|\[::1?\]|\[f[cd]|\[fe[89ab])/i;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const bound = (v, [dflt, max]) => { const n = Number(v); return Number.isFinite(n) && n > 0 ? Math.min(Math.floor(n), max) : dflt; };

// ---- robots.txt: the requested agent's group, else "*". Longest rule wins, allow wins a tie.
export function parseRobots(text) {
  const groups = []; let cur = null, inAgents = false;
  for (const raw of String(text).split(/\r?\n/)) {
    const m = /^\s*([A-Za-z-]+)\s*:\s*(.*?)\s*$/.exec(raw.replace(/#.*$/, ""));
    if (!m) continue;
    const k = m[1].toLowerCase(), v = m[2];
    if (k === "user-agent") { if (!inAgents) groups.push(cur = { agents: [], rules: [], delay: 0 }); cur.agents.push(v.toLowerCase()); inAgents = true; continue; }
    inAgents = false;
    if (!cur) continue;
    if ((k === "allow" || k === "disallow") && v) cur.rules.push({ allow: k === "allow", len: v.length, re: new RegExp("^" + v.replace(/[.+?^{}()|[\]\\]/g, "\\$&").replace(/\*/g, ".*")) });
    else if (k === "crawl-delay" && +v > 0) cur.delay = +v * 1000;
  }
  const g = groups.find((x) => x.agents.some((a) => a !== "*" && ROBOTS_AGENT.startsWith(a))) || groups.find((x) => x.agents.includes("*"));
  return {
    delay: g?.delay || 0,
    allowed(pathQuery) {
      let best = null;
      for (const r of g?.rules || []) if (r.re.test(pathQuery) && (!best || r.len > best.len || (r.len === best.len && r.allow))) best = r;
      return !best || best.allow;
    },
  };
}

async function get(url, sameOriginAs, state) {
  let cur = url;
  for (let hop = 0; hop < 5; hop++) {
    const r = await fetch(cur, { redirect: "manual", headers: { "User-Agent": UA, Accept: "text/html,text/plain;q=0.9,*/*;q=0.5" }, signal: AbortSignal.timeout(20000) });
    const loc = r.headers.get("location");
    if (r.status >= 300 && r.status < 400 && loc) {
      await r.body?.cancel();
      cur = new URL(loc, cur).href;
      if (!/^https?:/.test(cur) || (sameOriginAs && new URL(cur).origin !== sameOriginAs)) return { status: r.status, url: cur, offsite: true };
      continue;
    }
    const chunks = []; let n = 0, truncated = false;
    if (r.body) for await (const c of r.body) { n += c.length; state.bytes += c.length; if (n > PAGE_BYTES) { truncated = true; break; } chunks.push(c); }
    return { status: r.status, url: cur, type: r.headers.get("content-type") || "", retryAfter: r.headers.get("retry-after"), body: new TextDecoder().decode(Buffer.concat(chunks)), truncated };
  }
  throw new Error("too many redirects");
}

const links = (html, base) => {
  const out = [];
  for (const m of html.replace(/<(script|style|noscript|template)\b[\s\S]*?<\/\1>|<!--[\s\S]*?-->/gi, "").matchAll(/<a\b[^>]*>/gi)) {
    if (/\brel\s*=\s*["'][^"']*nofollow/i.test(m[0])) continue;
    const h = /\bhref\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))/i.exec(m[0]);
    if (!h) continue;
    try { const u = new URL((h[1] ?? h[2] ?? h[3]).replace(/&amp;/g, "&"), base); u.hash = ""; if (/^https?:$/.test(u.protocol)) out.push(u.href); } catch {}
  }
  return out;
};

export async function crawl(a, mapOnly = false) {
  let start;
  try { start = new URL(a.url); } catch { throw new Error("url required (absolute http/https)"); }
  if (!/^https?:$/.test(start.protocol)) throw new Error("only http/https can be crawled");
  start.hash = "";
  const maxPages = bound(a.max_pages, LIMITS.max_pages), maxDepth = a.max_depth === 0 ? 0 : bound(a.max_depth, LIMITS.max_depth), deadlineMs = bound(a.deadline_ms, LIMITS.deadline_ms);
  const sameOrigin = a.same_origin !== false, origin = start.origin, startPrivate = PRIVATE.test(start.hostname);
  const delay = Math.max(MIN_DELAY, Number(a.delay_ms) || DEFAULT_DELAY), pageChars = Number(a.max_chars) || 4000;
  const rx = (s, n) => { if (!s) return null; try { return new RegExp(s); } catch { throw new Error(`${n} is not a valid regex`); } };
  const include = rx(a.include, "include"), exclude = rx(a.exclude, "exclude");

  const began = Date.now(), state = { bytes: 0 }, robots = new Map();
  const pages = [], skipped = { robots: 0, offsite: 0, filtered: 0, not_html: 0 }, errors = [], notes = [];
  const seen = new Set([start.href]), queue = [{ url: start.href, depth: 0 }];
  let stopped = "done", last = 0, output = 0, wait = delay;
  const pace = async (ms) => { const gap = last + ms - Date.now(); if (gap > 0) await sleep(gap); last = Date.now(); };

  const robotsFor = async (o) => {
    if (robots.has(o)) return robots.get(o);
    let r = parseRobots("");
    if (a.respect_robots !== false) {
      try {
        await pace(wait);
        const g = await get(o + "/robots.txt", null, state); last = Date.now();
        if (g.status === 200 && !g.offsite) r = parseRobots(g.body);
        else if (g.status >= 500) { r = parseRobots("User-agent: *\nDisallow: /"); notes.push(`${o}/robots.txt HTTP ${g.status}: treated as disallow`); }
      } catch (e) { notes.push(`${o}/robots.txt unreadable (${e.message}): continuing`); }
    }
    robots.set(o, r);
    return r;
  };

  while (queue.length) {
    if (pages.length >= maxPages) { stopped = "max_pages"; break; }
    if (Date.now() - began > deadlineMs) { stopped = "deadline"; break; }
    if (state.bytes > TOTAL_BYTES) { stopped = "byte_budget"; break; }
    const { url, depth } = queue.shift(), u = new URL(url);
    const rob = await robotsFor(u.origin);
    wait = Math.max(delay, Math.min(rob.delay, MAX_ROBOTS_DELAY));
    if (!rob.allowed(u.pathname + u.search)) { skipped.robots++; continue; }
    await pace(wait);
    let g;
    try { g = await get(url, sameOrigin ? origin : null, state); last = Date.now(); }
    catch (e) { last = Date.now(); errors.push({ url, error: e.cause?.code || e.message }); continue; }
    if (g.offsite) { skipped.offsite++; continue; }
    if (g.status === 429 || g.status === 503) { stopped = `rate_limited (HTTP ${g.status}${g.retryAfter ? ", Retry-After " + g.retryAfter : ""})`; break; }
    if (g.status >= 400) { errors.push({ url, status: g.status }); continue; }
    const isHtml = /html|xml/i.test(g.type), isText = /^text\//i.test(g.type);
    if (!isHtml && !isText) { skipped.not_html++; continue; }
    const page = { url: g.url, depth, status: g.status, title: isHtml ? toMarkdown((/<title\b[^>]*>([\s\S]*?)<\/title>/i.exec(g.body) || [])[1] || "") : "" };
    if (!mapOnly) {
      const md = isHtml ? toMarkdown(g.body) : g.body, room = Math.max(0, Math.min(pageChars, OUTPUT_CHARS - output));
      page.markdown = md.slice(0, room);
      if (md.length > room || g.truncated) page.truncated = true;
      output += page.markdown.length;
    }
    pages.push(page);
    if (isHtml && depth < maxDepth) for (const l of links(g.body, g.url)) {
      if (seen.has(l)) continue;
      seen.add(l);
      const lu = new URL(l);
      if (sameOrigin ? lu.origin !== origin : (PRIVATE.test(lu.hostname) && !startPrivate)) { skipped.offsite++; continue; }
      if (SKIP_EXT.test(lu.pathname)) { skipped.not_html++; continue; }
      if ((include && !include.test(l)) || (exclude && exclude.test(l))) { skipped.filtered++; continue; }
      queue.push({ url: l, depth: depth + 1 });
    }
  }
  const result = { start: start.href, same_origin: sameOrigin, stopped, queued_left: queue.length, elapsed_ms: Date.now() - began, skipped, errors: errors.slice(0, 20), ...(notes.length ? { notes } : {}) };
  return JSON.stringify(mapOnly ? { ...result, urls: pages.map((p) => ({ url: p.url, title: p.title, depth: p.depth })) } : { ...result, pages });
}
