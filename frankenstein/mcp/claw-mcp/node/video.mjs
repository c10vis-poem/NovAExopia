// claw.scrape action=video: metadata and transcript from captions. Uses yt-dlp when it is on PATH; falls back to the page itself
// (YouTube player JSON, or <track> and og: tags). Speech-to-text for videos with no captions is not here: no local whisper on this phone.
import { mkdtempSync, readdirSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pick } from "./wire.mjs";
import { run } from "./platform.mjs";

const UA = "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/124 Mobile Safari/537.36";
const ytdlp = () => process.env.CLAW_YTDLP || "yt-dlp";
const stamp = (sec) => { const s = Math.floor(sec), h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), p = (n) => String(n).padStart(2, "0"); return `[${h ? h + ":" + p(m) : m}:${p(s % 60)}]`; };
const fetchText = async (url) => { const r = await fetch(url, { headers: { "User-Agent": UA }, signal: AbortSignal.timeout(30000) }); if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.text(); };
const unesc = (s) => s.replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#0?39;/g, "'").replace(/&nbsp;/g, " ");

// VTT, including YouTube's rolling captions where each cue repeats the previous line.
export function parseVtt(text) {
  const cues = [];
  for (const block of String(text).replace(/\r/g, "").split(/\n{2,}/)) {
    const lines = block.split("\n"), i = lines.findIndex((l) => l.includes("-->"));
    if (i < 0) continue;
    const m = /(?:(\d+):)?(\d+):(\d+)[.,](\d+)\s*-->/.exec(lines[i]);
    if (!m) continue;
    const start = +(m[1] || 0) * 3600 + +m[2] * 60 + +m[3];
    for (const raw of lines.slice(i + 1)) {
      const t = unesc(raw.replace(/<[^>]*>/g, "")).trim();
      if (t && !cues.slice(-3).some((c) => c.text === t)) cues.push({ start, text: t });
    }
  }
  return cues;
}
export function parseJson3(text) {
  const cues = [];
  for (const e of JSON.parse(text).events || []) {
    const t = (e.segs || []).map((s) => s.utf8 || "").join("").replace(/\s+/g, " ").trim();
    if (t) cues.push({ start: (e.tStartMs || 0) / 1000, text: t });
  }
  return cues;
}
const parseAny = (body) => body.trimStart().startsWith("{") ? parseJson3(body) : parseVtt(body);

// One shape for tracks: { lang, auto, formats: [{ ext, url }] }.
function tracksFromYtdlp(info) {
  const conv = (o, auto) => Object.entries(o || {}).filter(([l]) => l !== "live_chat").map(([lang, fs]) => ({ lang, auto, formats: (fs || []).filter((f) => f.url).map((f) => ({ ext: f.ext, url: f.url })) }));
  return [...conv(info.subtitles, false), ...conv(info.automatic_captions, true)];
}
function chooseTrack(tracks, want) {
  const manual = tracks.filter((t) => !t.auto), auto = tracks.filter((t) => t.auto);
  const match = (list, l) => list.find((t) => t.lang === l) || list.find((t) => t.lang.startsWith(l + "-")) || list.find((t) => t.lang.split("-")[0] === l.split("-")[0]);
  if (want) return match(manual, want) || match(auto, want + "-orig") || match(auto, want) || { missing: want };
  const en = match(manual, "en") || auto.find((t) => t.lang === "en-orig") || match(auto, "en");
  if (en) return en;
  if (manual.length === 1) return manual[0];
  const orig = auto.find((t) => t.lang.endsWith("-orig"));
  if (!manual.length && orig) return orig;
  if (!manual.length && auto.length === 1) return auto[0];
  return { ask: (manual.length ? manual : auto).map((t) => t.lang) };
}
async function fetchTrack(track) {
  let lastErr;
  for (const ext of ["json3", "vtt"]) {
    const f = track.formats.find((x) => x.ext === ext);
    if (!f) continue;
    try { const cues = parseAny(await fetchText(f.url)); if (cues.length) return { cues, format: ext }; lastErr = new Error("empty track"); }
    catch (e) { lastErr = e; }
  }
  throw lastErr || new Error("no json3 or vtt track");
}
// When a direct caption URL is refused, let yt-dlp fetch the file its own way.
async function ytdlpTrack(url, track) {
  const dir = mkdtempSync(join(process.env.TMPDIR || tmpdir(), "claw-video-"));
  try {
    await run(ytdlp(), ["--skip-download", "--no-playlist", "--no-warnings", track.auto ? "--write-auto-subs" : "--write-subs", "--sub-langs", track.lang, "--sub-format", "vtt", "-o", join(dir, "v"), "--", url], 120000);
    const f = readdirSync(dir).find((n) => n.endsWith(".vtt"));
    if (!f) throw new Error("yt-dlp wrote no caption file");
    return { cues: parseVtt(readFileSync(join(dir, f), "utf8")), format: "vtt" };
  } finally { rmSync(dir, { recursive: true, force: true }); }
}

function sliceJson(html, marker) {
  const at = html.search(marker); if (at < 0) return null;
  const start = html.indexOf("{", at); if (start < 0) return null;
  let depth = 0, str = false, esc = false;
  for (let i = start; i < html.length; i++) {
    const c = html[i];
    if (str) { if (esc) esc = false; else if (c === "\\") esc = true; else if (c === '"') str = false; continue; }
    if (c === '"') str = true; else if (c === "{") depth++; else if (c === "}" && --depth === 0) { try { return JSON.parse(html.slice(start, i + 1)); } catch { return null; } }
  }
  return null;
}
async function fromPage(url) {
  const html = await fetchText(url);
  const yt = sliceJson(html, /ytInitialPlayerResponse\s*=\s*\{/);
  if (yt?.videoDetails) {
    const d = yt.videoDetails;
    const tracks = (yt.captions?.playerCaptionsTracklistRenderer?.captionTracks || []).map((t) => ({
      lang: t.languageCode + (t.kind === "asr" ? "-orig" : ""), auto: t.kind === "asr",
      formats: [{ ext: "json3", url: t.baseUrl + (t.baseUrl.includes("?") ? "&" : "?") + "fmt=json3" }, { ext: "vtt", url: t.baseUrl + (t.baseUrl.includes("?") ? "&" : "?") + "fmt=vtt" }],
    }));
    return { tracks, meta: { id: d.videoId, title: d.title, uploader: d.author, duration: +d.lengthSeconds || null, view_count: +d.viewCount || null, description: d.shortDescription || "", url } };
  }
  const meta = (name) => { const m = new RegExp(`<meta[^>]+(?:property|name)=["']${name}["'][^>]*content=["']([^"']*)`, "i").exec(html); return m ? unesc(m[1]) : null; };
  const tracks = [...html.matchAll(/<track\b[^>]*>/gi)].flatMap((m) => {
    const src = /\bsrc=["']([^"']+)/i.exec(m[0])?.[1], lang = /\bsrclang=["']([^"']+)/i.exec(m[0])?.[1] || "und";
    if (!src || !/\bkind=["'](?:captions|subtitles)/i.test(m[0])) return [];
    return [{ lang, auto: false, formats: [{ ext: "vtt", url: new URL(unesc(src), url).href }] }];
  });
  const title = meta("og:title") || (/<title\b[^>]*>([^<]*)/i.exec(html) || [])[1];
  if (!title && !tracks.length) throw new Error("no video metadata or captions on the page");
  return { tracks, meta: { title: title ? unesc(title) : null, description: meta("og:description"), url } };
}

export async function video(a) {
  let u; try { u = new URL(a.url); } catch { throw new Error("url required (absolute http/https)"); }
  if (!/^https?:$/.test(u.protocol)) throw new Error("only http/https video URLs");
  const maxChars = Number(a.max_chars) || 40000, notes = [];
  let tracks, meta, via;
  try {
    const raw = await run(ytdlp(), ["--dump-single-json", "--skip-download", "--no-playlist", "--no-warnings", "--socket-timeout", "20", "--", u.href], 120000);
    const info = JSON.parse(raw);
    tracks = tracksFromYtdlp(info);
    meta = { id: info.id, title: info.title, uploader: info.uploader || info.channel, duration: info.duration, upload_date: info.upload_date, view_count: info.view_count, description: (info.description || "").slice(0, 2000), chapters: info.chapters || undefined, extractor: info.extractor, url: info.webpage_url || u.href };
    via = "yt-dlp";
  } catch (e) {
    notes.push("yt-dlp: " + e.message.split("\n").filter((l) => /error/i.test(l)).concat(e.message.split("\n")[0])[0].slice(0, 300));
    try { ({ tracks, meta } = await fromPage(u.href)); via = "page"; }
    catch (e2) { throw new Error(`no video data for ${u.href}. ${notes[0]}; page: ${e2.message}`); }
  }
  meta.description = (meta.description || "").slice(0, 2000);
  const base = { metadata: meta, via, languages: { captions: tracks.filter((t) => !t.auto).map((t) => t.lang), auto: tracks.filter((t) => t.auto).map((t) => t.lang).slice(0, 12) } };
  if (a.metadata_only) return JSON.stringify(base);

  const reply = (transcript) => JSON.stringify({ ...base, transcript, ...(notes.length ? { notes } : {}) });
  if (!tracks.length) { notes.push("no captions on this video; speech-to-text is not available in claw"); return reply(null); }
  const t = chooseTrack(tracks, a.lang);
  if (t.missing) { notes.push(`no captions in "${t.missing}"`); return reply(null); }
  if (t.ask) return pick(reply(null), "This video has no English captions. Which language?", t.ask);

  let got;
  try { got = await fetchTrack(t); }
  catch (e) {
    notes.push(`direct caption fetch failed (${e.message})`);
    if (via !== "yt-dlp") return reply(null);
    try { got = await ytdlpTrack(u.href, t); }
    catch (e2) { notes.push(`yt-dlp caption fetch failed (${e2.message.split("\n")[0].slice(0, 200)})`); return reply(null); }
  }
  const text = got.cues.map((c) => (a.timestamps === false ? "" : stamp(c.start) + " ") + c.text).join("\n");
  return reply({ lang: t.lang, kind: t.auto ? "auto" : "captions", format: got.format, cues: got.cues.length, chars: text.length, truncated: text.length > maxChars, text: text.slice(0, maxChars) });
}
