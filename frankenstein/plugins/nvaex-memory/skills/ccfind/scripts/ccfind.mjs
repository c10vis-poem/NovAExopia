#!/usr/bin/env node
// ccfind - BM25 full-text search over local Claude Code transcripts.
// Subcommands: index, search, show, stats. Trimmed fold (install/open/pick/bench dropped).
// No network calls. Reads ~/.claude/projects/*/*.jsonl, writes ~/.claude/ccfind/.

import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import readline from 'node:readline';
import zlib from 'node:zlib';

const HOME = os.homedir();
// Where Claude Code keeps its state. `CLAUDE_CONFIG_DIR` is Claude Code's own
// override, so honouring it is the difference between finding a user's history
// and reporting that they have none; `CCFIND_CONFIG_DIR` points ccfind at a
// different corpus than the CLI is using, which is how the demo is recorded
// against a synthetic history instead of somebody's real one.
const CONFIG = process.env.CCFIND_CONFIG_DIR || process.env.CLAUDE_CONFIG_DIR
             || path.join(HOME, '.claude');
const PROJECTS = path.join(CONFIG, 'projects');
const STORE = path.join(CONFIG, 'ccfind');
const DOCS = path.join(STORE, 'docs.jsonl');
const INDEX = path.join(STORE, 'index.json.gz');
const STATE = path.join(STORE, 'state.json');
// Held for the length of one rebuild. SKILL.md has every session run `index`
// before it searches, so two sessions starting together is the ordinary case,
// not a corner one.
const LOCK = path.join(STORE, 'index.lock');

// Field weights: a hit in what the user actually asked outranks a hit in
// scrollback from a grep that happened to print the word.
const FIELD_WEIGHT = { title: 3.5, prompt: 3.0, answer: 1.5, thinking: 0.7, tool: 1.0, output: 0.5, summary: 0.4 };
const FIELDS = ['title', 'prompt', 'answer', 'thinking', 'tool', 'output', 'summary'];
const IDXV = 4;
const CHUNK = 1000;           // chars per indexed chunk
const MAX_TOOL_INPUT = 2000;  // truncate tool args
const MAX_TOOL_OUTPUT = 16000;// truncate tool results
const K1 = 1.2, B = 0.75;
const MAX_DF_RATIO = 0.4;     // ignore terms present in >40% of chunks
const SUBTOKEN_QUERY_WEIGHT = 0.35; // "kube-vip" must beat every stray "kube"

// ---------------------------------------------------------------- tokenizer

const SPLIT = /[^\p{L}\p{N}_.-]+/u;
const CAMEL = /(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])/;

function variants(raw) {
  // Returns [full, ...subtokens] for one whitespace-delimited word.
  const t = raw.replace(/^[.\-]+|[.\-]+$/g, '');
  if (!t || t.length > 64) return [];
  const out = [t.toLowerCase()];
  if (/[._-]/.test(t)) {
    for (const p of t.split(/[._-]+/)) if (p.length > 1) out.push(p.toLowerCase());
  }
  if (CAMEL.test(t)) {
    for (const p of t.split(CAMEL)) if (p.length > 1) out.push(p.toLowerCase());
  }
  return [...new Set(out)];
}

export function tokenize(text) {
  const out = [];
  for (const raw of String(text).split(SPLIT)) {
    if (raw) out.push(...variants(raw));
  }
  return out;
}

// Query tokens carry weights: the compound the user typed counts full, the
// pieces it decomposes into count little. Without this, "kube-vip" ranks every
// exchange that ever said "kube" alongside the ones about the VIP itself.
function queryTerms(q) {
  const w = new Map();
  const full = new Set();
  for (const raw of String(q).split(SPLIT)) {
    if (!raw) continue;
    const vs = variants(raw);
    if (!vs.length) continue;
    full.add(vs[0]);
    w.set(vs[0], Math.max(w.get(vs[0]) || 0, 1.0));
    for (const sub of vs.slice(1)) {
      if (full.has(sub)) continue;
      w.set(sub, Math.max(w.get(sub) || 0, SUBTOKEN_QUERY_WEIGHT));
    }
  }
  for (const f of full) w.set(f, 1.0);
  return { weights: w, full: [...full] };
}

// ---------------------------------------------------------------- extraction

const B64ISH = /^[A-Za-z0-9+/=\s]{400,}$/;

// Injected context is not something the user typed. Indexing it as a prompt
// (weight 3.0) would rank hook boilerplate above real questions, and showing it
// as the "ask" line makes a correct hit look wrong.
const INJECTED = [
  /<system-reminder>[\s\S]*?<\/system-reminder>/g,
  /<local-command-stdout>[\s\S]*?<\/local-command-stdout>/g,
  /<local-command-stderr>[\s\S]*?<\/local-command-stderr>/g,
  /<command-name>[\s\S]*?<\/command-name>/g,
  /<command-message>[\s\S]*?<\/command-message>/g,
  /<local-command-caveat>[\s\S]*?<\/local-command-caveat>/g,
  // `/ccfind which session had the coredns fix` - the words inside the tag are
  // the user's actual question. Dropping the whole element threw away the prompt of
  // every slash-command turn; only the wrapper is boilerplate.
  /<\/?command-args>/g,
  /<user-prompt-submit-hook>[\s\S]*?<\/user-prompt-submit-hook>/g,
  /^[ \t]*(?:UserPromptSubmit|SessionStart)[^\n]*hook[^\n]*$/gm,
  /\[Image #\d+\]/g,
];

function cleanPrompt(text) {
  let t = String(text);
  for (const re of INJECTED) t = t.replace(re, ' ');
  return t.trim();
}

function textOfToolResult(content) {
  if (typeof content === 'string') return content;
  if (Array.isArray(content)) {
    return content
      .map((b) => (b && typeof b === 'object' && b.type === 'text' ? b.text : ''))
      .filter(Boolean)
      .join('\n');
  }
  return '';
}

function* fieldsOf(entry) {
  const msg = entry.message;
  if (!msg || typeof msg !== 'object') return;
  const role = msg.role;
  const content = msg.content;
  // A compaction summary is written by Claude, not asked by the user, and it
  // repeats every topic of the session it replaces. Indexed as a prompt it would
  // let a continuation outrank the session that did the work, and it would
  // supply the "ask" line. Own field, lowest weight: still findable, never wins.
  const userField = entry.isCompactSummary ? 'summary' : 'prompt';
  // A meta turn is injected, not typed: the body of a skill the model loaded, the
  // "messages below were generated by the user" caveat, an image-cache path,
  // "Continue from where you left off." 145 of 969 user turns in the test corpus.
  // Indexed as prompts they rank a skill's own README above the question it
  // answered - which is exactly what happened to this tool's own transcript.
  if (entry.isMeta && role === 'user') return;

  if (typeof content === 'string') {
    if (role === 'user') {
      const c = cleanPrompt(content);
      if (c) yield { field: userField, text: c };
    }
    return;
  }
  if (!Array.isArray(content)) return;

  for (const b of content) {
    if (!b || typeof b !== 'object') continue;
    switch (b.type) {
      case 'text': {
        if (role === 'user') {
          const c = cleanPrompt(b.text || '');
          if (c) yield { field: userField, text: c };
        } else if (b.text) {
          yield { field: 'answer', text: b.text };
        }
        break;
      }
      case 'thinking':
        if (b.thinking) yield { field: 'thinking', text: b.thinking };
        break;
      case 'tool_use': {
        let args = '';
        try { args = JSON.stringify(b.input ?? {}); } catch { args = ''; }
        yield { field: 'tool', text: `${b.name || ''} ${args.slice(0, MAX_TOOL_INPUT)}` };
        break;
      }
      case 'tool_result': {
        const t = textOfToolResult(b.content).slice(0, MAX_TOOL_OUTPUT);
        if (t && !B64ISH.test(t)) yield { field: 'output', text: t };
        break;
      }
      default:
        break; // image, server_tool_use, advisor_tool_result (encrypted): nothing to index
    }
  }
}

function chunks(text) {
  const s = text.replace(/\s+/g, ' ').trim();
  if (!s) return [];
  if (s.length <= CHUNK) return [s];
  const out = [];
  let i = 0;
  while (i < s.length) {
    let end = Math.min(i + CHUNK, s.length);
    if (end < s.length) {
      const sp = s.lastIndexOf(' ', end);
      if (sp > i + CHUNK * 0.6) end = sp;
    }
    out.push(s.slice(i, end));
    i = end;
  }
  return out;
}

// ---------------------------------------------------------------- index build

// The index on disk, if it was built from exactly these transcripts as they are
// now; null when anything changed, is missing, or cannot be read. An index
// written by an older field layout cannot be trusted even when every transcript
// is unchanged: field ids shift and weights move with them.
function currentIndex(files) {
  const prev = readJSON(STATE, {});
  if (Object.keys(prev).length !== files.length) return null;
  for (const rel of files) {
    const st = safeStat(path.join(PROJECTS, rel));
    const p = prev[rel];
    if (!st || !p || p.size !== st.size || p.mtimeMs !== st.mtimeMs) return null;
  }
  if (!fs.existsSync(DOCS) || !fs.existsSync(INDEX)) return null;
  let cached = null;
  try { cached = readIndex(); } catch { /* half-written or corrupt: rebuild */ }
  // The document file the offsets point into has to be the one written with
  // them; a size recorded at build time is the cheap way to know. Indexes from
  // before the size was recorded are still taken at their word.
  const docsOk = cached?.docsBytes === undefined || cached.docsBytes === safeStat(DOCS)?.size;
  if (cached && cached.v === IDXV && docsOk) return cached;
  _index = null;
  return null;
}

// One rebuild at a time. Two builders writing the same files interleave, and
// whichever wins the last rename leaves a document list that belongs to the
// other's index. A lock left behind by a process that died is broken as soon as
// its pid is gone, and after a few minutes regardless, so a crash costs a wait
// and not a store that never rebuilds again.
const LOCK_STALE_MS = 5 * 60 * 1000;
function alive(pid) {
  try { process.kill(pid, 0); return true; } catch (e) { return e.code === 'EPERM'; }
}
async function lockStore() {
  const t0 = Date.now();
  for (;;) {
    try {
      const fd = fs.openSync(LOCK, 'wx');
      fs.writeSync(fd, String(process.pid));
      fs.closeSync(fd);
      return () => { try { fs.unlinkSync(LOCK); } catch { /* already gone */ } };
    } catch (e) {
      if (e.code !== 'EEXIST') throw e;
    }
    const st = safeStat(LOCK);
    const pid = +(readText(LOCK) || '');
    if (!st || (Number.isInteger(pid) && pid > 0 && !alive(pid)) || Date.now() - st.mtimeMs > LOCK_STALE_MS) {
      try { fs.unlinkSync(LOCK); } catch { /* the holder let go first */ }
      continue;
    }
    if (Date.now() - t0 > LOCK_STALE_MS) {
      throw new Error(`another ccfind has been rebuilding the index for over five minutes - if none is running, remove ${LOCK}`);
    }
    await new Promise((r) => setTimeout(r, 100));
  }
}

async function buildIndex({ full = false, quiet = false } = {}) {
  const t0 = Date.now();
  fs.mkdirSync(STORE, { recursive: true });

  const files = [];
  for (const dir of safeReaddir(PROJECTS)) {
    const dp = path.join(PROJECTS, dir);
    if (!safeStat(dp)?.isDirectory()) continue;
    for (const f of safeReaddir(dp)) {
      if (f.endsWith('.jsonl')) files.push(path.join(dir, f));
    }
  }

  let cached = full ? null : currentIndex(files);
  if (cached) {
    if (!quiet) console.error(`ccfind: index up to date (${files.length} transcripts)`);
    return cached;
  }

  const unlock = await lockStore();
  // Everything is staged under names no other process uses and renamed into
  // place only once complete, so a reader never sees a file that is half
  // written, and a build that dies leaves the previous index untouched.
  const tmp = { docs: `${DOCS}.${process.pid}.tmp`, index: `${INDEX}.${process.pid}.tmp` };
  try {
    // The wait may have been for another process doing exactly this rebuild.
    cached = full ? null : currentIndex(files);
    if (cached) {
      if (!quiet) console.error(`ccfind: index up to date (${files.length} transcripts, rebuilt by another ccfind)`);
      return cached;
    }
    return await rebuild(files, tmp, t0, quiet);
  } finally {
    for (const p of Object.values(tmp)) { try { fs.unlinkSync(p); } catch { /* renamed or never written */ } }
    unlock();
  }
}

// v0.1 rebuilds whole corpus on any change: roughly 13 MB/s measured, and a
// correct incremental merge is only worth writing once the on-disk format
// settles.
async function rebuild(files, tmp, t0, quiet) {
  const docsFd = fs.openSync(tmp.docs, 'w');
  const state = {};
  const sessions = [];      // {id, title, project, cwd, branch, first, last, n}
  const sessionIdx = new Map();
  const exchanges = [];     // {si, t, ts, n}
  const dx = [];            // doc -> exchange index
  const dfld = [];          // doc -> field id
  const dl = [];
  const offsets = [];
  const postings = new Map();
  let docId = 0, offset = 0, bytesRead = 0;

  const pushDoc = (xi, field, text, ts, sc) => {
    const toks = tokenize(text);
    if (!toks.length) return;
    const tf = new Map();
    for (const t of toks) tf.set(t, (tf.get(t) || 0) + 1);
    const w = FIELD_WEIGHT[field] ?? 1.0;
    for (const [t, n] of tf) {
      let arr = postings.get(t);
      if (!arr) { arr = []; postings.set(t, arr); }
      arr.push(docId, n * w);
    }
    const buf = Buffer.from(JSON.stringify({ t: text, ts, sc: sc ? 1 : 0 }) + '\n', 'utf8');
    fs.writeSync(docsFd, buf);
    offsets.push(offset, buf.length);
    offset += buf.length;
    dl.push(toks.length * w);
    dx.push(xi);
    dfld.push(FIELDS.indexOf(field));
    exchanges[xi].n++;
    docId++;
  };

  for (const rel of files) {
    const abs = path.join(PROJECTS, rel);
    const st = safeStat(abs);
    if (!st) continue;
    state[rel] = { size: st.size, mtimeMs: st.mtimeMs };
    bytesRead += st.size;

    const project = path.dirname(rel);
    const sid = path.basename(rel, '.jsonl');
    const si = sessions.length;
    sessionIdx.set(sid, si);
    sessions.push({ id: sid, title: null, project, cwd: null, branch: null, first: null, last: null, n: 0 });

    // Every exchange this file pushes carries this file's si, and exchanges is
    // append-only, so the file's own slice is exactly [x0, exchanges.length).
    // That turns "which exchanges belong to this session" from a scan of the
    // whole array per file into two integers.
    const x0 = exchanges.length;
    let xi = -1;
    let sawPrompt = false;

    const rl = readline.createInterface({
      input: fs.createReadStream(abs, { encoding: 'utf8' }),
      crlfDelay: Infinity,
    });

    for await (const line of rl) {
      if (!line) continue;
      let e;
      try { e = JSON.parse(line); } catch { continue; }

      // Session titles: /rename wins over the model-written one.
      if (e.type === 'custom-title' && e.customTitle) sessions[si].title = e.customTitle;
      else if (e.type === 'ai-title' && e.aiTitle && !sessions[si].title) sessions[si].title = e.aiTitle;
      if (e.type !== 'user' && e.type !== 'assistant') continue;

      const s = sessions[si];
      if (e.cwd && !s.cwd) s.cwd = e.cwd;
      if (e.gitBranch && !s.branch) s.branch = e.gitBranch;
      if (e.timestamp) { if (!s.first) s.first = e.timestamp; s.last = e.timestamp; }

      for (const { field, text } of fieldsOf(e)) {
        if (!text) continue;
        // A user prompt opens a new exchange; the tool calls and answers that
        // follow hang off it, which is how people remember conversations.
        if (field === 'prompt') {
          if (sawPrompt || xi === -1) {
            exchanges.push({ si, t: text.replace(/\s+/g, ' ').trim().slice(0, 220), ts: e.timestamp || null, n: 0 });
            xi = exchanges.length - 1;
          }
          sawPrompt = true;
        } else if (xi === -1) {
          exchanges.push({ si, t: '(session start)', ts: e.timestamp || null, n: 0 });
          xi = exchanges.length - 1;
          sawPrompt = false;
        }
        for (const chunk of chunks(text)) pushDoc(xi, field, chunk, e.timestamp || null, e.isSidechain);
      }
    }

    // Index the title against the session's first exchange so a search for the
    // topic finds the session even when the wording only exists in the title.
    if (sessions[si].title) {
      let xt = exchanges.length > x0 ? x0 : -1;
      if (xt === -1) {
        exchanges.push({ si, t: sessions[si].title, ts: sessions[si].first, n: 0 });
        xt = exchanges.length - 1;
      }
      pushDoc(xt, 'title', sessions[si].title, sessions[si].first, false);
    }
    sessions[si].n = exchanges.length - x0;
  }
  fs.closeSync(docsFd);
  const docsBytes = fs.statSync(tmp.docs).size;

  const N = docId;
  const avgdl = N ? dl.reduce((a, b) => a + b, 0) / N : 0;
  const maxDf = Math.max(4, Math.floor(N * MAX_DF_RATIO));
  const post = {};
  let dropped = 0;
  for (const [t, arr] of postings) {
    if (arr.length / 2 > maxDf) { dropped++; continue; }
    post[t] = arr;
  }

  const index = { v: IDXV, N, avgdl, dl, offsets, dx, dfld, exchanges, sessions,
                  postings: post, built: new Date().toISOString(), bytesRead, files: files.length,
                  docsBytes };
  fs.writeFileSync(tmp.index, zlib.gzipSync(Buffer.from(JSON.stringify(index)), { level: 6 }));
  // Documents first, then the index that points into them, then the state that
  // says both are current. A crash between any two steps leaves something the
  // next run either reads whole or rebuilds; state last is what makes the
  // "up to date" answer trustworthy.
  fs.renameSync(tmp.docs, DOCS);
  fs.renameSync(tmp.index, INDEX);
  fs.writeFileSync(STATE, JSON.stringify(state));
  _index = index;

  if (!quiet) {
    console.error(
      `ccfind: indexed ${files.length} sessions, ` +
      `${(bytesRead / 1048576).toFixed(1)} MB of transcripts, in ${Date.now() - t0} ms` +
      (dropped ? ` (${dropped} words too common to be useful)` : '')
    );
  }
  return index;
}

// ---------------------------------------------------------------- search

let _index = null;
function readIndex() {
  if (_index) return _index;
  if (!fs.existsSync(INDEX)) return null;
  try {
    _index = JSON.parse(zlib.gunzipSync(fs.readFileSync(INDEX)));
  } catch {
    throw new Error('the index is unreadable - run: ccfind.mjs index');
  }
  return _index;
}

function readDoc(idx, id) {
  const off = idx.offsets[id * 2], len = idx.offsets[id * 2 + 1];
  let fd = null;
  try {
    fd = fs.openSync(DOCS, 'r');
    const buf = Buffer.alloc(len);
    const got = fs.readSync(fd, buf, 0, len, off);
    return JSON.parse(buf.toString('utf8', 0, got));
  } catch {
    // Offsets that do not land on a document mean the two files were not
    // written together.
    throw new Error('the index and its documents do not match - run: ccfind.mjs index');
  } finally { if (fd !== null) fs.closeSync(fd); }
}

// For the commands that need an index and nothing else: a missing or broken
// one is a usage problem to say in a sentence, not a stack trace.
function requireIndex() {
  let idx = null;
  try { idx = readIndex(); } catch (e) { console.error(`ccfind: ${e.message}`); process.exit(1); }
  if (!idx) { console.error('ccfind: no index - run: ccfind.mjs index'); process.exit(1); }
  return idx;
}

function scoreDocs(idx, query) {
  const { weights, full } = queryTerms(query);
  const scores = new Map();
  const hitFull = new Map(); // doc -> Set(full term) : coverage counts only what was typed
  const idfOf = new Map();
  for (const [t, qw] of weights) {
    const arr = idx.postings[t];
    if (!arr) continue;
    const df = arr.length / 2;
    const idf = Math.log(1 + (idx.N - df + 0.5) / (df + 0.5));
    const isFull = qw === 1.0;
    if (isFull) idfOf.set(t, idf);
    for (let i = 0; i < arr.length; i += 2) {
      const id = arr[i], tf = arr[i + 1];
      const norm = (tf * (K1 + 1)) / (tf + K1 * (1 - B + B * (idx.dl[id] / idx.avgdl)));
      scores.set(id, (scores.get(id) || 0) + qw * idf * norm);
      if (isFull) {
        let s = hitFull.get(id);
        if (!s) { s = new Set(); hitFull.set(id, s); }
        s.add(t);
      }
    }
  }
  return { scores, hitFull, full, weights, idfOf };
}

// Roll chunk scores up one level: the best chunk dominates, corroborating
// chunks add a capped bonus so a long noisy session cannot out-sum a precise
// short one. Coverage of the typed terms multiplies - it is the strongest
// signal that a conversation is about the thing asked for.
// Coverage is weighted by idf squared, not by term count. A query like
// "image-gc-high threshold on the node" is answered by the one session holding
// that identifier, even when it never spells out the other three words - which
// is the usual shape when the identifier is English and the sentence around it
// is not. Plain idf is not enough: three ordinary words still out-sum one rare
// identifier. Squaring makes the rarest term of a query
// dominate its own coverage, which is what a person means when they type it.
function rollup(entries, idfOf, restCap = 1.5, restWeight = 0.25) {
  let total = 0;
  for (const v of idfOf.values()) total += v * v;
  const out = [];
  for (const g of entries) {
    const rest = Math.min(g.rest, g.best.sc * restCap);
    let got = 0;
    for (const t of g.terms) { const v = idfOf.get(t) || 0; got += v * v; }
    const cov = total > 0 ? got / total : 1;
    g.score = (g.best.sc + restWeight * rest) * (0.35 + 0.65 * cov);
    g.cov = cov;
    out.push(g);
  }
  out.sort((a, b) => b.score - a.score);
  return out;
}

function search(query, opts = {}) {
  const idx = readIndex();
  if (!idx) throw new Error('no index yet; run: ccfind.mjs index');
  const limit = opts.limit ?? 10;
  const group = opts.group === 'exchange' ? 'exchange' : 'session';
  const { scores, hitFull, full, idfOf } = scoreDocs(idx, query);
  const empty = { terms: full, group, hits: [], relevant: 0, weak: 0, total: 0,
                  docsScored: 0, exchangesScored: 0, sessionsScored: 0 };
  if (!scores.size) return empty;

  // --field restricts the search to that field rather than only requiring the
  // winning chunk to sit in it. A low-weight field never wins a roll-up, so the
  // post-filter made `--field summary` and `--field thinking` unsearchable.
  if (opts.field) {
    const fi = FIELDS.indexOf(opts.field);
    if (fi < 0) throw new Error(`unknown field: ${opts.field} (have ${FIELDS.join('|')})`);
    for (const id of [...scores.keys()]) if (idx.dfld[id] !== fi) scores.delete(id);
    if (!scores.size) return empty;
  }

  const byX = new Map();
  for (const [id, sc] of scores) {
    const xi = idx.dx[id];
    let g = byX.get(xi);
    if (!g) { g = { xi, best: { id, sc }, rest: 0, terms: new Set(), docs: 0 }; byX.set(xi, g); }
    if (sc > g.best.sc) { g.rest += g.best.sc; g.best = { id, sc }; } else g.rest += sc;
    g.docs++;
    for (const t of hitFull.get(id) || []) g.terms.add(t);
  }
  const xRanked = rollup([...byX.values()], idfOf);

  let groups;
  if (group === 'exchange') {
    groups = xRanked.map((g) => ({ ...g, si: idx.exchanges[g.xi].si }));
  } else {
    const byS = new Map();
    for (const g of xRanked) {
      const si = idx.exchanges[g.xi].si;
      let s = byS.get(si);
      if (!s) { s = { si, best: { id: g.best.id, sc: g.score, xi: g.xi }, rest: 0, terms: new Set(), docs: 0 }; byS.set(si, s); }
      else if (g.score > s.best.sc) { s.rest += s.best.sc; s.best = { id: g.best.id, sc: g.score, xi: g.xi }; }
      else s.rest += g.score;
      s.docs += g.docs;
      for (const t of g.terms) s.terms.add(t);
    }
    groups = rollup([...byS.values()], idfOf, 1.0, 0.15);
    for (const g of groups) g.xi = g.best.xi;
  }

  // filters
  const sessOf = (g) => idx.sessions[g.si ?? idx.exchanges[g.xi].si];
  if (opts.project) {
    const q = opts.project.toLowerCase();
    groups = groups.filter((g) => {
      const s = sessOf(g);
      return (s.project || '').toLowerCase().includes(q) || (s.cwd || '').toLowerCase().includes(q);
    });
  }
  if (opts.session) groups = groups.filter((g) => sessOf(g).id.startsWith(opts.session));
  if (opts.exclude) {
    const ex = Array.isArray(opts.exclude) ? opts.exclude : [opts.exclude];
    groups = groups.filter((g) => !ex.some((e) => e && sessOf(g).id.startsWith(e)));
  }
  if (opts.days) {
    const cut = Date.now() - opts.days * 86400000;
    groups = groups.filter((g) => {
      const ts = idx.exchanges[g.xi].ts || sessOf(g).last;
      return ts ? Date.parse(ts) >= cut : false;
    });
  }

  // The turn a session opened with is the cheapest honest description of it:
  // exchanges are pushed in file order, so the first one per session is it.
  const firstOf = new Map();
  for (let i = 0; i < idx.exchanges.length; i++) {
    const si = idx.exchanges[i].si;
    if (!firstOf.has(si)) firstOf.set(si, idx.exchanges[i]);
  }

  // BM25 has no notion of "not relevant": every session holding one query word
  // gets a score, so a 25-row list is one answer plus 24 sessions that happen to
  // share the word "restart". The gate keeps the hits scoring within a fraction
  // of the top one and hands back the rest as a count, so the caller states a
  // measured number instead of eyeballing the table.
  //
  // 0.25 is where the sweep over 12 ground-truth queries settles: it drops 169
  // of 173 irrelevant hits for 0.03 of P@3, where 0.3 buys two more of those
  // 173 at 0.06. What it costs is always the same shape - a session that
  // mentions the identifier once in passing, which grep-based ground truth
  // scores as relevant and a reader does not. The top hit is exempt by
  // construction: a search that matched something always answers with something.
  const WEAK_BAR = 0.25;
  let relevant = groups.length;
  if (!opts.all && groups.length) {
    const bar = groups[0].score * WEAK_BAR;
    relevant = 1;
    while (relevant < groups.length && groups[relevant].score >= bar) relevant++;
  }

  const hits = groups.slice(0, Math.min(limit, relevant)).map((g) => {
    const x = idx.exchanges[g.xi];
    const s = sessOf(g);
    const open = firstOf.get(g.si ?? idx.exchanges[g.xi].si);
    const doc = readDoc(idx, g.best.id);
    return {
      score: +g.score.toFixed(2),
      coverage: +g.cov.toFixed(2),
      chunks: g.docs,
      title: s.title,
      session: s.id,
      project: s.project,
      cwd: s.cwd,
      branch: s.branch,
      when: x.ts || s.last,
      prompt: x.t,
      field: FIELDS[idx.dfld[g.best.id]],
      sidechain: !!doc.sc,
      snippet: snippet(doc.t, full),
      opening: open && open.t !== x.t ? open.t : null,
      turns: s.n || null,
      // Two different things, and the difference is the whole point: `/resume`
      // is a built-in slash command (argumentHint "[conversation id or search
      // term]") that switches this window to that session, while
      // `claude --resume` starts a separate run in a terminal.
      open: `/resume ${s.id}`,
      resume: `claude --resume ${s.id}`,
    };
  });
  // `total` stays what it always was - everything that matched after the
  // filters - so a caller can still say how wide the field was. `relevant` is
  // what survived the gate, `weak` what it cut.
  return { terms: full, group, hits, relevant, weak: groups.length - relevant,
           total: groups.length, docsScored: scores.size,
           exchangesScored: byX.size, sessionsScored: new Set(xRanked.map((g) => idx.exchanges[g.xi].si)).size };
}

function snippet(text, terms, width = 260) {
  const low = text.toLowerCase();
  let best = 0, bestScore = -1;
  for (let i = 0; i < Math.max(1, low.length - width / 2); i += 40) {
    const win = low.slice(i, i + width);
    let s = 0;
    for (const t of terms) if (win.includes(t)) s++;
    if (s > bestScore) { bestScore = s; best = i; }
  }
  const from = Math.max(0, best - 20);
  let out = text.slice(from, from + width);
  if (from > 0) out = '...' + out;
  if (from + width < text.length) out += '...';
  return out;
}

// ---------------------------------------------------------------- cli

function readJSON(p, dflt) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch { return dflt; }
}
function safeReaddir(p) { try { return fs.readdirSync(p); } catch { return []; } }
function safeStat(p) { try { return fs.statSync(p); } catch { return null; } }
function readText(p) { try { return fs.readFileSync(p, 'utf8'); } catch { return null; } }

function parseArgs(argv) {
  const o = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const k = a.slice(2);
      const next = argv[i + 1];
      if (next && !next.startsWith('--')) { o[k] = next; i++; } else o[k] = true;
    } else o._.push(a);
  }
  return o;
}

// A count flag that fails to parse falls back to the default instead of
// poisoning a slice with NaN ("--limit abc" silently showing zero hits).
// A bare flag (parseArgs leaves it as true) is not a count of one either.
function posInt(v, dflt) {
  if (v === true) return dflt;
  const n = Math.floor(+v);
  return Number.isFinite(n) && n > 0 ? n : dflt;
}

// Same idea for a window of days, except fractions are meaningful: --days 0.5
// is the last twelve hours. Not posInt, which would floor that to 0 and quietly
// drop the filter the user asked for. Unlike posInt, a bare --days is kept as
// one day: "what did I do today" is the question it is short for.
function posNum(v, dflt) {
  const n = +v;
  return Number.isFinite(n) && n > 0 ? n : dflt;
}

// Plain-text output is what a first-time reader sees, so it spells things out:
// where the session lived, the words the user themselves used, and which part of
// the conversation the match landed in. --json carries the raw numbers.
const FIELD_LABEL = {
  title: 'the session name',
  prompt: 'your own question',
  answer: 'the answer',
  thinking: 'the reasoning',
  tool: 'a command that ran',
  output: 'command output',
  summary: 'the session summary',
};

function wrap(text, width, indent) {
  const out = [];
  let line = '';
  for (const w of String(text).split(/\s+/)) {
    if (line && line.length + 1 + w.length > width) { out.push(line); line = w; }
    else line = line ? `${line} ${w}` : w;
  }
  if (line) out.push(line);
  return out.map((l) => indent + l).join('\n');
}

function shortPath(p) {
  if (!p) return null;
  return p === HOME ? '~' : p.startsWith(HOME + path.sep) ? '~' + p.slice(HOME.length) : p;
}


function human(res) {
  if (!res.hits.length) {
    console.log(`nothing matched: ${res.terms.join(' ')}`);
    return;
  }
  const width = Math.min(Math.max(process.stdout.columns || 88, 60), 100);
  // res.total is the count after filters, so it never promises a session the
  // caller cannot actually reach (the current session is excluded by default).
  const total = res.total ?? (res.group === 'session' ? res.sessionsScored : res.exchangesScored);
  const unit = res.group === 'session' ? 'session' : 'turn';
  // The gate already dropped the long tail, so the header counts what it kept:
  // saying "best 4 of 61" when 57 of those 61 were one shared common word reads
  // as a search that found plenty and showed little.
  const rel = res.relevant ?? total;
  console.log(res.hits.length < rel
    ? `best ${res.hits.length} of ${rel} relevant ${unit}s:\n`
    : `${rel} relevant ${unit}${rel === 1 ? '' : 's'}:\n`);
  let n = 0;
  for (const h of res.hits) {
    n++;
    const when = h.when ? h.when.slice(0, 16).replace('T', ' ') : 'date unknown';
    const meta = [when, shortPath(h.cwd) || h.project];
    if (h.branch) meta.push(h.branch);
    if (h.sidechain) meta.push('subagent');
    const words = res.terms.length;
    const found = Math.round(h.coverage * words);
    const cov = found >= words
      ? `all ${words} word${words === 1 ? '' : 's'} present`
      : `${found} of ${words} words present`;
    console.log(`${n}. ${h.title || h.project}`);
    console.log(`   ${meta.join('  ')}`);
    console.log(`   score ${h.score}, ${cov}`);
    if (h.prompt) console.log(wrap(`you asked: "${h.prompt}"`, width - 3, '   '));
    if (h.opening) console.log(wrap(`session began: "${h.opening}"`, width - 3, '   '));
    console.log(`   matched in ${FIELD_LABEL[h.field] || h.field}:`);
    console.log(wrap(h.snippet, width - 5, '     '));
    console.log(`   open it:   ${h.open}${process.env.CLAUDECODE ? '' : `   (in a terminal: ${h.resume})`}\n`);
  }
  // Two different numbers, so two lines: relevant hits that --limit cut off are
  // worth re-running for, weak ones are worth knowing about but not printing.
  const more = (res.relevant ?? res.total ?? res.hits.length) - res.hits.length;
  if (more > 0) console.log(`${more} more relevant - re-run with --limit ${res.relevant}`);
  if (res.weak > 0) console.log(`${res.weak} weak match${res.weak === 1 ? '' : 'es'} scored far below the top hit and were hidden - --all shows them`);
}

// The finished answer, built here rather than by the model. When the model wrote
// the table itself, every model wrote a different one: one dropped it under a
// terse house style, another wrote no text next to a tool call at all. Text the
// model only has to paste comes out the same whichever model is asking, so the
// skill pastes this verbatim inside a code fence - which terse styles also leave
// alone.
const LABELS = {
  en: {
    head: ['#', 'Session', 'Date', 'Project', 'id', 'Requests', 'Matched'],
    none: (q) => `nothing matched: ${q}`,
    counts: (rel, total, weak, shown) => `${rel} relevant of ${total} matched; ${weak} were weak`
      + (shown !== rel ? `; showing ${shown}` : ''),
    open: 'Open',
  },
  ru: {
    head: ['#', 'Сессия', 'Дата', 'Проект', 'id', 'Запросы', 'Фрагмент'],
    none: (q) => `ничего не найдено: ${q}`,
    counts: (rel, total, weak, shown) => `релевантных: ${rel} из ${total}, слабых: ${weak}`
      + (shown !== rel ? `, показано: ${shown}` : ''),
    open: 'Открыть',
  },
};

function detectLang(text) {
  return /[Ѐ-ӿ]/.test(text) ? 'ru' : 'en';
}

// Terminal cells, not string length: CJK and emoji take two, combining marks none.
function cells(s) {
  let n = 0;
  for (const ch of s) {
    const c = ch.codePointAt(0);
    if ((c >= 0x300 && c <= 0x36f) || c === 0x200d || (c >= 0xfe00 && c <= 0xfe0f)) continue;
    n += (c >= 0x1100 && c <= 0x115f) || (c >= 0x2e80 && c <= 0xa4cf) || (c >= 0xac00 && c <= 0xd7a3)
      || (c >= 0xf900 && c <= 0xfaff) || (c >= 0xfe30 && c <= 0xfe4f) || (c >= 0xff00 && c <= 0xff60)
      || (c >= 0xffe0 && c <= 0xffe6) || (c >= 0x1f300 && c <= 0x1faff) || (c >= 0x20000 && c <= 0x3fffd) ? 2 : 1;
  }
  return n;
}

function fit(s, width) {
  if (cells(s) <= width) return s;
  let out = '';
  for (const ch of s) {
    if (cells(out + ch) > width - 1) break;
    out += ch;
  }
  return out + '…';
}

// Every cell is one line of plain text: control characters (ANSI escapes from
// tool output) would break the alignment, and a run of three backticks would
// close the code fence the skill pastes this into.
const clean = (s) => String(s || '').replace(/\x1b\[[0-9;?]*[A-Za-z]/g, '').replace(/\s+/g, ' ')
  .replace(/[\x00-\x1f\x7f]/g, '')
  .replace(/`{3,}/g, '``').trim();

const pad = (s, width) => s + ' '.repeat(Math.max(0, width - cells(s)));

// A fragment of the snippet that starts just before the first query word, so the
// cut keeps the part that matched. Verbatim apart from collapsed whitespace.
function fragment(text, terms, width) {
  const raw = String(text || '');
  const cut = raw.endsWith('...');
  const flat = clean(raw.replace(/^\.\.\./, '').replace(/\.\.\.$/, ''));
  const low = flat.toLowerCase();
  let at = -1;
  for (const t of terms) {
    const i = low.indexOf(t);
    if (i >= 0 && (at < 0 || i < at)) at = i;
  }
  // A few words of lead-in, starting on a word boundary.
  let from = Math.max(0, at - 24);
  if (from > 0) {
    const sp = flat.indexOf(' ', from);
    from = sp >= 0 && sp < at ? sp + 1 : at;
  }
  const body = (from > 0 ? '…' : '') + flat.slice(from);
  return cells(body) <= width && cut ? fit(body + '…', width) : fit(body, width);
}

const projectOf = (h) => clean((h.cwd && path.basename(h.cwd)) || h.project);
// No title yet: the turn the session began from says more than the project
// name, which every session in the same directory shares.
const nameOf = (h) => clean(h.title || h.opening || h.prompt) || projectOf(h);

// `compact` is the same answer with no column alignment, for the picker's
// question string, which is not guaranteed to keep runs of spaces.
function render(res, q, lang, { compact = false } = {}) {
  const L = LABELS[lang] || LABELS.en;
  if (!res.hits.length) return L.none(q);
  const year = String(new Date().getFullYear());
  const rows = res.hits.map((h, i) => {
    const when = !h.when ? '?' : h.when.startsWith(year) ? h.when.slice(5, 10) : h.when.slice(2, 10);
    return [String(i + 1), fit(nameOf(h), 18), when, fit(projectOf(h), 14),
            h.session.slice(0, 8), String(h.turns ?? '')];
  });
  const total = res.total ?? res.hits.length;
  const rel = res.relevant ?? total;
  const tail = ['', L.counts(rel, total, res.weak ?? 0, res.hits.length),
                '', `${L.open}: ${nameOf(res.hits[0])}`, res.hits[0].open];
  if (compact) {
    const [, ...head] = L.head;
    return res.hits.map((h, i) => {
      const [n, ...cells_] = rows[i];
      const parts = cells_.map((c, k) => (k === 4 ? `${head[k]}: ${c}` : c));
      return `${n}. ${parts.join(' · ')} · "${fragment(h.snippet, res.terms, 60)}"`;
    }).concat(tail).join('\n');
  }
  const widths = L.head.slice(0, 6).map((head, c) => Math.max(cells(head), ...rows.map((r) => cells(r[c]))));
  const gap = '  ';
  // Capped at 110 cells so the block does not wrap in an ordinary terminal.
  const rest = Math.max(20, 110 - widths.reduce((a, b) => a + b, 0) - gap.length * 6);
  const line = (r) => r.map((cell, c) => (c < 6 ? pad(cell, widths[c]) : cell)).join(gap).trimEnd();
  const out = [line(L.head), line(widths.map((w) => '-'.repeat(w)).concat('-'.repeat(Math.min(rest, 20))))];
  res.hits.forEach((h, i) => out.push(line([...rows[i], `"${fragment(h.snippet, res.terms, rest - 2)}"`])));
  return out.concat(tail).join('\n');
}

const args = parseArgs(process.argv.slice(2));
const cmd = args._[0] || 'search';

if (cmd === 'index') {
  try {
    await buildIndex({ full: !!args.full });
  } catch (e) {
    console.error(`ccfind: ${e.message}`);
    process.exit(1);
  }
} else if (cmd === 'stats') {
  const idx = requireIndex();
  console.log(JSON.stringify({
    built: idx.built, transcripts: idx.files, sessions: idx.sessions.length,
    exchanges: idx.exchanges.length, chunks: idx.N,
    terms: Object.keys(idx.postings).length, avgdl: +idx.avgdl.toFixed(1),
    mbRead: +(idx.bytesRead / 1048576).toFixed(1),
    indexMb: +((safeStat(INDEX)?.size ?? 0) / 1048576).toFixed(2),
    docsMb: +((safeStat(DOCS)?.size ?? 0) / 1048576).toFixed(2),
    titled: idx.sessions.filter((s) => s.title).length,
  }, null, 2));
} else if (cmd === 'show') {
  // Reading one session's shape without opening the transcript: what it started
  // from, every turn in order, so a picked search hit can be understood in place.
  const want = args._[1];
  if (!want) { console.error('usage: ccfind.mjs show <session-id> [--turns N] [--json]'); process.exit(1); }
  const idx = requireIndex();
  const si = idx.sessions.findIndex((x) => x.id.startsWith(want));
  if (si === -1) { console.error(`ccfind: no session starting with ${want}`); process.exit(1); }
  const ses = idx.sessions[si];
  const turns = idx.exchanges
    .map((x, i) => ({ ...x, i }))
    .filter((x) => x.si === si && x.t && x.t !== '(session start)');
  const cap = posInt(args.turns, 40);
  const shown = turns.slice(0, cap);
  if (args.json) {
    console.log(JSON.stringify({
      session: ses.id, title: ses.title, project: ses.project, cwd: ses.cwd,
      branch: ses.branch, first: ses.first, last: ses.last, turns: turns.length,
      shown: shown.map((x) => ({ when: x.ts, prompt: x.t })),
      open: `/resume ${ses.id}`,
      resume: `claude --resume ${ses.id}`,
    }, null, 2));
  } else {
    const width = Math.min(Math.max(process.stdout.columns || 88, 60), 100);
    const day = (t) => (t ? t.slice(0, 16).replace('T', ' ') : '?');
    console.log(`${ses.title || ses.project}`);
    console.log(`${day(ses.first)} to ${day(ses.last)}  ${shortPath(ses.cwd) || ses.project}` +
                `${ses.branch ? '  ' + ses.branch : ''}  ${turns.length} turn${turns.length === 1 ? '' : 's'}`);
    console.log(`open it: /resume ${ses.id}   (in a terminal: claude --resume ${ses.id})\n`);
    console.log('what you asked, in order:');
    let n = 0;
    for (const x of shown) {
      n++;
      console.log(wrap(`${String(n).padStart(2)}. ${day(x.ts).slice(11) || '  '}  ${x.t}`, width - 4, '  '));
    }
    if (turns.length > shown.length) {
      console.log(`\n${turns.length - shown.length} more turns - re-run with --turns ${turns.length}`);
    }
  }
} else {
  const q = (cmd === 'search' ? args._.slice(1) : args._).join(' ');
  if (!q) {
    console.error('usage: ccfind.mjs search <query> [--limit N] [--group session|exchange]');
    console.error('                              [--project S] [--session ID] [--days N] [--field F]');
    console.error('                              [--exclude ID[,ID...]] [--self] [--all] [--json]');
    console.error('                              [--lang en|ru]');
    process.exit(1);
  }
  // A garbled --days used to disable the filter silently (NaN is falsy) and a
  // negative one silently matched nothing. Both now mean "no date filter", and
  // say so on stderr so stdout stays clean JSON.
  const days = posNum(args.days, null);
  if (args.days !== undefined && days === null) {
    console.error(`ccfind: ignoring --days ${args.days} - not a positive number of days`);
  }
  // The same courtesy for the other flags: a value that cannot be used is
  // dropped and said so, never quietly turned into something else.
  const given = (v) => (v === true ? '' : ` ${v}`);
  const limit = posInt(args.limit, 10);
  if (args.limit !== undefined && posInt(args.limit, null) === null) {
    console.error(`ccfind: ignoring --limit${given(args.limit)} - not a positive count`);
  }
  const group = args.group === 'exchange' || args.group === 'session' ? args.group : 'session';
  if (args.group !== undefined && group !== args.group) {
    console.error(`ccfind: ignoring --group${given(args.group)} - it is session or exchange`);
  }
  for (const flag of ['project', 'session', 'field', 'exclude']) {
    if (args[flag] === true) console.error(`ccfind: ignoring --${flag} - it needs a value`);
  }
  let res;
  try {
    res = search(q, {
      limit,
      group,
      project: typeof args.project === 'string' ? args.project : null,
      session: typeof args.session === 'string' ? args.session : null,
      field: typeof args.field === 'string' ? args.field : null,
      // The session doing the searching is never the answer to its own question.
      // Comma-separated so a caller can drop several known-irrelevant sessions at
      // once (a benchmark excluding its own scratch runs, a retry of a bad session).
      // --self lifts only the automatic self-exclusion; an explicit --exclude
      // list stays honored either way.
      exclude: [...(typeof args.exclude === 'string' ? args.exclude.split(',') : []),
                ...(args.self ? [] : [process.env.CLAUDE_CODE_SESSION_ID || null,
                                      process.env.CLAUDE_SESSION_ID || null])]
               .map((s) => s && s.trim()).filter(Boolean),
      days,
      // Everything BM25 scored, gate and all. For "did I ever mention X at all",
      // where a single passing reference is the answer.
      all: !!args.all,
    });
  } catch (e) {
    // A typo in a flag or a missing index is a usage problem, not a crash.
    console.error(`ccfind: ${e.message}`);
    process.exit(1);
  }
  if (args.json) {
    const asked = typeof args.lang === 'string' ? args.lang.toLowerCase() : null;
    const lang = asked && Object.hasOwn(LABELS, asked) ? asked : detectLang(q);
    if (args.lang !== undefined && lang !== asked) {
      console.error(`ccfind: ignoring --lang${given(args.lang)} - it is ${Object.keys(LABELS).join(' or ')}`);
    }
    const out = { ...res, lang, rendered: render(res, q, lang),
                  renderedCompact: render(res, q, lang, { compact: true }) };
    console.log(JSON.stringify(out, null, 2));
  } else human(res);
}
