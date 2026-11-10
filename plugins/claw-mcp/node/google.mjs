// Local Google route: Drive, Gmail, Calendar over REST, one token file per account, so the claude.ai connectors are not needed.
// Token file: $CLAW_GOOGLE_DIR/google-<account>.json (default ~/.config/claw-mcp), mode 0600, never in a repo:
//   {client_id, client_secret, refresh_token}   refreshed as needed, also accepts gcloud "authorized_user" files
//   {access_token, expiry?}                     used as is until it expires
// Writes are limited to Drive create, Gmail draft, Calendar create, and need confirm=true. Nothing sends, deletes or shares.
// Every value read from a token file is registered with the redactor; server.mjs passes all output through it.
import { readdirSync, readFileSync, statSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { toMarkdown } from "./md.mjs";
import { ClawError, addSecret, pick } from "./wire.mjs";

const dir = () => process.env.CLAW_GOOGLE_DIR || join(homedir(), ".config", "claw-mcp");
// Tests point every Google host at one local fake. Only loopback may stand in, so a stray env var cannot send tokens elsewhere.
function bases() {
  const o = process.env.CLAW_GOOGLE_BASE;
  if (!o) return { token: "https://oauth2.googleapis.com/token", drive: "https://www.googleapis.com/drive/v3", upload: "https://www.googleapis.com/upload/drive/v3", gmail: "https://gmail.googleapis.com/gmail/v1", calendar: "https://www.googleapis.com/calendar/v3" };
  if (!/^http:\/\/127\.0\.0\.1:\d+(\/|$)/.test(o)) throw new Error("CLAW_GOOGLE_BASE must be a http://127.0.0.1 address");
  return { token: o + "/token", drive: o + "/drive/v3", upload: o + "/upload/drive/v3", gmail: o + "/gmail/v1", calendar: o + "/calendar/v3" };
}
const accounts = () => { try { return readdirSync(dir()).map((f) => /^google-([\w.@+-]+)\.json$/.exec(f)?.[1]).filter(Boolean).sort(); } catch { return []; } };

function credentials(account) {
  if (!/^[\w.@+-]+$/.test(account) || account.includes("..")) throw new Error("bad account name");
  const f = join(dir(), `google-${account}.json`);
  let st; try { st = statSync(f); } catch { throw new Error(`no Google credentials for account "${account}" at ${f}. Create the file by hand: {"client_id","client_secret","refresh_token"}, mode 600.`); }
  if (st.mode & 0o077) throw new Error(`${f} is readable by others; run chmod 600 on it. Not using it.`);
  let c; try { c = JSON.parse(readFileSync(f, "utf8")); } catch { throw new Error(`${f} is not valid JSON`); }
  for (const k of ["client_secret", "refresh_token", "access_token"]) addSecret(c[k]);
  return c;
}

const cache = new Map();
async function accessToken(account, force = false) {
  const hit = cache.get(account);
  if (hit && !force && hit.exp > Date.now() + 60000) return hit.token;
  const c = credentials(account);
  if (c.refresh_token && c.client_id) {
    const r = await fetch(bases().token, { method: "POST", body: new URLSearchParams({ client_id: c.client_id, client_secret: c.client_secret || "", refresh_token: c.refresh_token, grant_type: "refresh_token" }), signal: AbortSignal.timeout(20000) });
    let t = {}; try { t = await r.json(); } catch {}
    if (!t.access_token) throw new Error(`Google token refresh failed for "${account}" (HTTP ${r.status}): ${t.error_description || t.error || "no access_token"}`);
    addSecret(t.access_token);
    cache.set(account, { token: t.access_token, exp: Date.now() + (t.expires_in || 3600) * 1000 });
    return t.access_token;
  }
  const exp = c.expiry ? Date.parse(c.expiry) : Infinity;
  if (c.access_token && !force && exp > Date.now() + 60000) { cache.set(account, { token: c.access_token, exp }); return c.access_token; }
  throw new Error(`Google credentials for "${account}" have no refresh_token and the access_token is ${c.access_token ? "expired or rejected" : "missing"}`);
}

function client(account) {
  const send = async (url, init = {}, retried = false) => {
    const r = await fetch(url, { ...init, headers: { Authorization: "Bearer " + await accessToken(account, retried), ...init.headers }, signal: AbortSignal.timeout(60000) });
    if (r.status === 401 && !retried) { await r.body?.cancel(); return send(url, init, true); } // token revoked or expired early
    return r;
  };
  const text = async (url, init) => { const r = await send(url, init); const b = await r.text(); if (!r.ok) throw new Error(`Google HTTP ${r.status} from ${new URL(url).pathname}: ${b.slice(0, 300)}`); return b; };
  return { send, text, json: async (url, init) => JSON.parse(await text(url, init)) };
}
const qs = (o) => new URLSearchParams(Object.entries(o).filter(([, v]) => v !== undefined && v !== null && v !== "")).toString();
const asJson = (o) => JSON.stringify(o);

// ---- Drive
const EXPORTS = { "application/vnd.google-apps.document": ["text/markdown", "text/plain"], "application/vnd.google-apps.spreadsheet": ["text/csv"], "application/vnd.google-apps.presentation": ["text/plain"] };
const isText = (m) => /^text\/|json|xml|javascript|yaml|csv/i.test(m || "");
const DRIVE_FIELDS = "id,name,mimeType,size,modifiedTime,webViewLink,parents";
async function drive(g, a, b) {
  const op = a.op || (a.id ? "read" : "list"), max = a.max_chars || 20000, id = encodeURIComponent(a.id || "");
  if (op === "list") return asJson(await g.json(`${b.drive}/files?${qs({ q: a.query, pageSize: a.limit || 20, pageToken: a.page_token, fields: `nextPageToken,files(${DRIVE_FIELDS})`, supportsAllDrives: true, includeItemsFromAllDrives: true })}`));
  if (op === "create") {
    if (!a.name) throw new Error("drive create needs name");
    if (a.confirm !== true) return pick(`Would create Drive file "${a.name}". Repeat with confirm=true.`, `Create Drive file "${a.name}"?`, ["Create it", "Do not create"]);
    const bound = "claw" + Date.now(), mime = a.mime_type || "text/plain";
    if (/[\r\n]/.test(mime)) throw new Error("mime_type must not contain line breaks");
    const body = `--${bound}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n${JSON.stringify({ name: a.name, ...(a.folder ? { parents: [a.folder] } : {}) })}\r\n--${bound}\r\nContent-Type: ${mime}\r\n\r\n${a.content ?? ""}\r\n--${bound}--`;
    return asJson(await g.json(`${b.upload}/files?${qs({ uploadType: "multipart", fields: DRIVE_FIELDS, supportsAllDrives: true })}`, { method: "POST", headers: { "Content-Type": `multipart/related; boundary=${bound}` }, body }));
  }
  if (!["get", "read"].includes(op)) throw new Error("drive op must be list|get|read|create");
  if (!a.id) throw new Error(`drive ${op} needs id`);
  const meta = await g.json(`${b.drive}/files/${id}?${qs({ fields: DRIVE_FIELDS, supportsAllDrives: true })}`);
  if (op === "get") return asJson(meta);
  if (EXPORTS[meta.mimeType]) {
    let last;
    for (const mt of EXPORTS[meta.mimeType]) {
      const r = await g.send(`${b.drive}/files/${id}/export?${qs({ mimeType: mt })}`);
      const t = await r.text();
      if (r.ok) return asJson({ ...meta, exported_as: mt, content: t.slice(0, max), truncated: t.length > max });
      last = `HTTP ${r.status}`;
    }
    throw new Error(`Drive export failed: ${last}`);
  }
  if (meta.mimeType?.startsWith("application/vnd.google-apps.")) return asJson({ ...meta, content: null, note: "this Google file type has no text export" });
  if (!isText(meta.mimeType)) return asJson({ ...meta, content: null, note: "binary file, not printed; use rclone or Drive to download" });
  const t = await g.text(`${b.drive}/files/${id}?${qs({ alt: "media", supportsAllDrives: true })}`);
  return asJson({ ...meta, content: t.slice(0, max), truncated: t.length > max });
}

// ---- Gmail
const b64 = (s) => Buffer.from(s || "", "base64url").toString("utf8");
const header = (p, n) => p?.headers?.find((h) => h.name.toLowerCase() === n)?.value;
function bodyOf(part) {
  const walk = (p, type) => { if (p.mimeType === type && p.body?.data) return b64(p.body.data); for (const c of p.parts || []) { const r = walk(c, type); if (r) return r; } return ""; };
  return walk(part, "text/plain") || toMarkdown(walk(part, "text/html"));
}
const attachments = (p) => [...(p.filename ? [p.filename] : []), ...(p.parts || []).flatMap(attachments)];
const message = (m, max) => ({ id: m.id, threadId: m.threadId, labels: m.labelIds, from: header(m.payload, "from"), to: header(m.payload, "to"), subject: header(m.payload, "subject"), date: header(m.payload, "date"), attachments: attachments(m.payload), body: bodyOf(m.payload).slice(0, max) });
const noBreak = (s, n) => { if (/[\r\n]/.test(s || "")) throw new Error(`${n} must not contain line breaks`); return s; };
async function gmail(g, a, b) {
  const base = `${b.gmail}/users/me`, op = a.op || (a.id ? "get" : "list"), max = a.max_chars || 20000, id = encodeURIComponent(a.id || "");
  if (op === "list") {
    const l = await g.json(`${base}/messages?${qs({ q: a.query, maxResults: a.limit || 10, pageToken: a.page_token })}`);
    const rows = [];
    for (const m of l.messages || []) {
      const d = await g.json(`${base}/messages/${encodeURIComponent(m.id)}?format=metadata&metadataHeaders=From&metadataHeaders=Subject&metadataHeaders=Date`);
      rows.push({ id: d.id, threadId: d.threadId, from: header(d.payload, "from"), subject: header(d.payload, "subject"), date: header(d.payload, "date"), snippet: d.snippet });
    }
    return asJson({ messages: rows, nextPageToken: l.nextPageToken });
  }
  if (op === "get") { if (!a.id) throw new Error("gmail get needs id"); return asJson(message(await g.json(`${base}/messages/${id}?format=full`), max)); }
  if (op === "thread") { if (!a.id) throw new Error("gmail thread needs id"); const t = await g.json(`${base}/threads/${id}?format=full`); return asJson({ id: t.id, messages: (t.messages || []).map((m) => message(m, max)) }); }
  if (op === "labels") return asJson(await g.json(`${base}/labels`));
  if (op === "draft") {
    if (!a.to) throw new Error("gmail draft needs to");
    noBreak(a.to, "to"); noBreak(a.cc, "cc"); noBreak(a.subject, "subject");
    if (a.confirm !== true) return pick(`Would save a draft to ${a.to}, subject "${a.subject || ""}". Nothing is sent. Repeat with confirm=true.`, `Save Gmail draft to ${a.to}?`, ["Save the draft", "Do not save"]);
    const lines = [`To: ${a.to}`, ...(a.cc ? [`Cc: ${a.cc}`] : []), `Subject: =?UTF-8?B?${Buffer.from(a.subject || "").toString("base64")}?=`, "MIME-Version: 1.0", 'Content-Type: text/plain; charset="UTF-8"', "", a.body ?? ""];
    const raw = Buffer.from(lines.join("\r\n")).toString("base64url");
    return asJson(await g.json(`${base}/drafts`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message: { raw } }) }));
  }
  throw new Error("gmail op must be list|get|thread|labels|draft");
}

// ---- Calendar
const when = (s, n) => { if (!s) throw new Error(`calendar create needs ${n}`); return /^\d{4}-\d\d-\d\d$/.test(s) ? { date: s } : { dateTime: s }; };
async function calendar(g, a, b) {
  const cal = encodeURIComponent(a.calendar || "primary"), op = a.op || (a.id ? "get" : "list");
  if (op === "calendars") return asJson(await g.json(`${b.calendar}/users/me/calendarList`));
  if (op === "list") return asJson(await g.json(`${b.calendar}/calendars/${cal}/events?${qs({ q: a.query, maxResults: a.limit || 10, singleEvents: true, orderBy: "startTime", timeMin: a.time_min || new Date().toISOString(), timeMax: a.time_max, pageToken: a.page_token })}`));
  if (op === "get") { if (!a.id) throw new Error("calendar get needs id"); return asJson(await g.json(`${b.calendar}/calendars/${cal}/events/${encodeURIComponent(a.id)}`)); }
  if (op === "create") {
    if (!a.summary) throw new Error("calendar create needs summary");
    const event = { summary: a.summary, start: when(a.start, "start"), end: when(a.end, "end"), ...(a.description ? { description: a.description } : {}), ...(a.location ? { location: a.location } : {}) };
    if (a.confirm !== true) return pick(`Would create "${a.summary}" from ${a.start} to ${a.end}. No invitations are sent. Repeat with confirm=true.`, `Create calendar event "${a.summary}"?`, ["Create it", "Do not create"]);
    return asJson(await g.json(`${b.calendar}/calendars/${cal}/events?sendUpdates=none`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(event) }));
  }
  throw new Error("calendar op must be list|get|calendars|create");
}

export async function google(a) {
  const run = { drive, gmail, calendar }[a.service];
  if (!run) throw new Error("service must be drive|gmail|calendar");
  let account = a.account;
  if (!account) {
    const known = accounts();
    if (known.length > 1) throw new ClawError(`${known.length} Google accounts are set up. Repeat with account=<name>.`, { question: "Which Google account?", options: known.slice(0, 8) });
    account = known[0] || "default";
  }
  credentials(account); // clear error before any network call
  return run(client(account), a, bases());
}
