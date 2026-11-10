// Finish-pass checks. Each line says what it was proven against:
//   [real]  the real thing on this phone (OS sockets, Termux:API, adb and openssl binaries)
//   [fake]  a fake written for this test; proves the client side only
import { spawn, execFileSync } from "node:child_process";
import { chmodSync, existsSync, mkdirSync, statSync, writeFileSync, readFileSync } from "node:fs";
import { createHash, createPrivateKey, createPublicKey, generateKeyPairSync, randomBytes, X509Certificate } from "node:crypto";
import net from "node:net";
import { join } from "node:path";
import { fakeAdbd, keyFromAdbBlob } from "./fake-adbd.mjs";
import { site, google as fakeGoogle, GOOGLE } from "./fake-services.mjs";
import { adbPublicKeyB64, adbCertificatePem } from "../node/adb.mjs";
import { parseRobots } from "../node/crawl.mjs";
import { parseVtt } from "../node/video.mjs";

const [D, T] = process.argv.slice(2); let bad = 0;
const ck = (tag, n, ok, extra = "") => { console.log(`${ok ? "PASS" : "FAIL"} [${tag}] ${n}${ok ? "" : "  " + String(extra).slice(0, 600)}`); if (!ok) bad = 1; };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const everything = []; // every byte of every server output, scanned for secrets at the end

// Wire format: the real cards.ts when CLAW_CARDS_TS points at it, else this mirror (packages must stay self-contained).
const mirror = (text, tool) => {
  const m = /^CHOICE:\s*(.+)$/m.exec(text);
  if (m) { const [q, ...o] = m[1].split("|").map((s) => s.trim()).filter(Boolean); return q && o.length ? { question: q, options: o.slice(0, 8), tool } : null; }
  const j = /\{\s*"choice"\s*:\s*\{[\s\S]*?\}\s*\}/.exec(text);
  if (j) { try { const c = JSON.parse(j[0]).choice; if (typeof c?.question === "string" && c.options?.length) return { question: c.question, options: c.options.map(String).slice(0, 8), tool }; } catch {} }
  return null;
};
let parseChoice = mirror, parser = "mirror of cards.ts";
if (process.env.CLAW_CARDS_TS) { parseChoice = (await import(process.env.CLAW_CARDS_TS)).parseChoice; parser = "real cards.ts"; }
console.log("INFO CHOICE lines checked with: " + parser);

function server(env = {}) {
  const p = spawn("node", [D + "/node/server.mjs"], { env: { ...process.env, PATH: process.env.STUBPATH + ":" + process.env.PATH, CLAW_LISTEN: "off", ...env } });
  let buf = "", err = "", n = 0; const w = new Map();
  p.stdout.on("data", (d) => { const s = String(d); everything.push(s); buf += s; let i; while ((i = buf.indexOf("\n")) >= 0) { const m = JSON.parse(buf.slice(0, i)); buf = buf.slice(i + 1); w.get(m.id)?.(m); } });
  p.stderr.on("data", (d) => { everything.push(String(d)); err += d; });
  const rpc = (method, params) => new Promise((res) => { const id = ++n; w.set(id, res); p.stdin.write(JSON.stringify({ jsonrpc: "2.0", id, method, params }) + "\n"); });
  const call = async (name, args) => { const r = (await rpc("tools/call", { name, arguments: args })).result; return { err: !!r.isError, t: r.content[0].text }; };
  return { p, rpc, call, dev: (a) => call("claw.device", a), scr: (a) => call("claw.scrape", a), br: (a) => call("claw.browser", a), stderr: () => err,
    close: () => new Promise((res) => { p.on("close", res); p.stdin.end(); }) };
}
const J = (r) => { try { return JSON.parse(r.t.split("\nCHOICE:")[0]); } catch { return {}; } };

// One NDJSON client on the listener socket.
function client(target) {
  const s = net.connect(target); let buf = "", n = 0, onReq = null, closed = false; const w = new Map();
  s.setEncoding("utf8");
  s.on("data", (d) => { buf += d; let i; while ((i = buf.indexOf("\n")) >= 0) { const m = JSON.parse(buf.slice(0, i)); buf = buf.slice(i + 1); if (m.method) onReq?.(m, (o) => s.write(JSON.stringify({ jsonrpc: "2.0", id: m.id, ...o }) + "\n")); else w.get(m.id)?.(m); } });
  s.on("error", () => {}); s.on("close", () => { closed = true; for (const r of w.values()) r({ closed: true }); });
  return { rpc: (method, params) => new Promise((res) => { const id = ++n; w.set(id, res); s.write(JSON.stringify({ jsonrpc: "2.0", id, method, params }) + "\n"); }),
    ready: new Promise((r, j) => { s.once("connect", r); s.once("error", j); }), onRequest: (f) => { onReq = f; }, raw: s, isClosed: () => closed, end: () => new Promise((r) => { s.once("close", r); s.destroy(); }) };
}

// ======== 4. CHOICE lines
{
  const FAKE = process.env.FAKE;
  const s = server();
  await fetch(FAKE + "/_settabs?n=2");
  let r = await s.br({ action: "read" }), c = parseChoice(r.t, "claw.browser");
  ck("fake", "CHOICE: several tabs and none selected -> card, no guess", r.err && c?.question === "Which Chrome tab should claw use?" && c.options.length === 3, r.t);
  ck("fake", "CHOICE: a pipe in a tab title cannot add an option", c?.options.some((o) => o.includes("Tab 0")) && c?.options.length === 3, JSON.stringify(c));
  r = await s.br({ action: "eval", expression: "1+1", tab: c.options[0] });
  ck("fake", "CHOICE: the option text works as the answer (tab=<option>)", r.t === "2", r.t);
  r = await s.br({ action: "eval", expression: "1+1" }); ck("fake", "chosen tab stays current", r.t === "2", r.t);
  r = await s.br({ action: "click", selector: "#many" }); c = parseChoice(r.t, "claw.browser");
  ck("fake", "CHOICE: selector matching several elements -> card, no click", r.err && c?.options.length === 3 && c.options[1] === "index 1: Sec ond", r.t);
  r = await s.br({ action: "click", selector: "#many", index: 1 }); ck("fake", "index resolves the ambiguous selector", !r.err && /clicked/.test(r.t), r.t);
  r = await s.br({ action: "type", selector: "#pw", text: "hunter2secret" }); c = parseChoice(r.t, "claw.browser");
  ck("fake", "CHOICE: password field -> refused and card to sign in by hand", r.err && /never handles passwords/.test(r.t) && c?.options[0] === "I signed in, continue", r.t);
  const calls = await (await fetch(FAKE + "/_calls")).json();
  ck("fake", "password text never reached the wire", !JSON.stringify(calls).includes("hunter2secret"));
  await fetch(FAKE + "/_settabs?n=0"); await s.close();
  const off = server({ CDP_PORT: "1" }); r = await off.br({ action: "tabs" }); c = parseChoice(r.t, "claw.browser");
  ck("real", "CHOICE: Chrome unreachable -> card (real refused port)", r.err && c?.options[0] === "Chrome is open and forwarded, retry", r.t);
  await off.close();
  const two = server({ ADB_STUB_DEVICES: "aaa\tdevice\nbbb\tdevice\nccc\toffline" });
  r = await two.dev({ action: "adb", args: ["shell", "true"] }); c = parseChoice(r.t, "claw.device");
  ck("fake", "CHOICE: several adb devices -> card (stub adb)", r.err && c?.options.join() === "aaa,bbb", r.t);
  r = await two.dev({ action: "adb", args: ["-s", "aaa", "shell", "true"] }); ck("fake", "adb -s passes through (stub adb)", /STUBADB -s aaa shell true/.test(r.t), r.t);
  await two.close();
}

// ======== 1 + 2. Platform and listener
{
  const sock = join(T, "s", "claw.sock"), stateDir = join(T, "state1");
  mkdirSync(join(T, "s"), { recursive: true, mode: 0o700 });
  const s = server({ CLAW_LISTEN: "unix:" + sock, CLAW_STATE_DIR: stateDir });
  let st = J(await s.dev({ action: "platform" }));
  for (let i = 0; i < 50 && st.listener?.state !== "listening"; i++) { await sleep(50); st = J(await s.dev({ action: "platform" })); }
  ck("real", "listener binds a real unix socket", st.listener?.state === "listening" && existsSync(sock), JSON.stringify(st));
  ck("real", "socket file is mode 0600", (statSync(sock).mode & 0o777) === 0o600, (statSync(sock).mode & 0o777).toString(8));
  ck("fake", "before aesc connects, toast is served by termux (stub binary)", st.ops?.toast === "termux" && st.aesc.connected === false, JSON.stringify(st));
  let r = await s.dev({ action: "toast", args: ["one"] }); ck("fake", "termux backend runs termux-toast (stub binary)", r.t.startsWith("STUB:") && r.t.endsWith("one"), r.t);

  const c = client(sock); await c.ready;
  const list = await c.rpc("tools/list");
  ck("real", "socket round trip: tools/list returns the 6 tools", list.result?.tools?.length === 6, JSON.stringify(list).slice(0, 200));
  const viaSock = await c.rpc("tools/call", { name: "claw.workflows", arguments: { action: "list" } });
  ck("real", "socket round trip: tools/call runs a tool", viaSock.result?.content?.[0]?.text.includes("phone-status"), JSON.stringify(viaSock));
  // Fake Aesc peer registers and serves ops.
  const seen = [];
  c.onRequest((m, reply) => { seen.push(m); if (m.method === "device/exec") reply({ result: "aesc ran " + m.params.cmd + " " + m.params.args.join(" ") }); else if (m.params.op === "battery") reply({ result: JSON.stringify({ percentage: 77, from: "aesc" }) }); else if (m.params.op === "vibrate") reply({ error: { message: "no vibrator" } }); else reply({ result: "aesc did " + m.params.op + " " + m.params.args.join(",") }); });
  const reg = await c.rpc("aesc/register", { name: "aesc-test", ops: ["battery", "toast", "vibrate", "exec:adb"] });
  ck("fake", "aesc registers over the socket", reg.result?.registered?.length === 4, JSON.stringify(reg));
  st = J(await s.dev({ action: "platform" }));
  ck("fake", "platform picks aesc for its ops, termux for the rest", st.aesc?.name === "aesc-test" && st.ops.toast === "aesc" && (st.ops.notify === null || st.ops.notify === "termux"), JSON.stringify(st));
  r = await s.dev({ action: "toast", args: ["two"] });
  ck("fake", "toast round trips stdio -> claw -> aesc peer -> back", r.t === "aesc did toast two" && seen.at(-1).method === "device/call", r.t);
  r = await s.dev({ action: "battery" }); ck("fake", "battery served by aesc backend", JSON.parse(r.t).from === "aesc", r.t);
  r = await s.dev({ action: "adb-devices" }); ck("fake", "an outside tool Aesc registered runs through Aesc, not here", /aesc ran adb devices/.test(r.t), r.t);
  r = await s.dev({ action: "vibrate" }); ck("fake", "aesc error surfaces as tool error", r.err && /no vibrator/.test(r.t), r.t);
  await c.end();
  for (let i = 0; i < 40; i++) { st = J(await s.dev({ action: "platform" })); if (!st.aesc?.connected) break; await sleep(25); }
  ck("fake", "aesc disconnect falls back to termux at runtime", st.aesc?.connected === false && st.ops.toast === "termux", JSON.stringify(st));

  // Second server on the same path leaves the live one alone.
  const s2 = server({ CLAW_LISTEN: "unix:" + sock, CLAW_STATE_DIR: stateDir });
  let st2 = J(await s2.dev({ action: "platform" }));
  for (let i = 0; i < 50 && st2.listener?.state === "not started"; i++) { await sleep(50); st2 = J(await s2.dev({ action: "platform" })); }
  const still = client(sock); await still.ready; const ping = await still.rpc("ping");
  ck("real", "second claw does not steal a live socket", st2.listener?.state === "disabled" && !!ping.result, JSON.stringify(st2));
  await still.end(); await s2.close();
  // Oversize line drops the client, not the server.
  const big = client(sock); await big.ready; big.raw.write("x".repeat(1100000)); for (let i = 0; i < 100 && !big.isClosed(); i++) await sleep(20);
  r = await s.dev({ action: "platform" }); ck("real", "oversize line drops that client; server survives", big.isClosed() && !r.err);
  await s.close();
  ck("real", "socket file removed when the server exits", !existsSync(sock));
  // Stale socket file (killed server) is replaced.
  const k = server({ CLAW_LISTEN: "unix:" + sock, CLAW_STATE_DIR: stateDir });
  for (let i = 0; i < 100 && !existsSync(sock); i++) await sleep(20);
  await new Promise((res) => { k.p.on("close", res); k.p.kill("SIGKILL"); });
  const stale = existsSync(sock);
  const s3 = server({ CLAW_LISTEN: "unix:" + sock, CLAW_STATE_DIR: stateDir });
  let st3 = J(await s3.dev({ action: "platform" }));
  for (let i = 0; i < 50 && st3.listener?.state !== "listening"; i++) { await sleep(50); st3 = J(await s3.dev({ action: "platform" })); }
  ck("real", "stale socket file from a killed server is replaced", stale && st3.listener?.state === "listening", JSON.stringify(st3));
  await new Promise((res) => { s3.p.on("close", res); s3.p.kill("SIGTERM"); });
  ck("real", "SIGTERM exits and removes the socket", !existsSync(sock));

  // TCP: loopback only, token required.
  const tok = randomBytes(16).toString("hex");
  const t = server({ CLAW_LISTEN: "tcp:127.0.0.1:0", CLAW_LISTEN_TOKEN: tok, CLAW_STATE_DIR: stateDir });
  let ts = J(await t.dev({ action: "platform" }));
  for (let i = 0; i < 50 && ts.listener?.state !== "listening"; i++) { await sleep(50); ts = J(await t.dev({ action: "platform" })); }
  const port = ts.listener?.port;
  ck("real", "tcp listener binds 127.0.0.1 only", ts.listener?.host === "127.0.0.1" && port > 0, JSON.stringify(ts));
  const noauth = client({ host: "127.0.0.1", port }); await noauth.ready; let a = await noauth.rpc("tools/list");
  ck("real", "tcp refuses a client without the token", a.error?.code === -32001, JSON.stringify(a)); await noauth.end();
  const wrong = client({ host: "127.0.0.1", port }); await wrong.ready; a = await wrong.rpc("auth", { token: "0".repeat(32) });
  ck("real", "tcp refuses a wrong token", a.error?.code === -32001, JSON.stringify(a)); await wrong.end();
  const right = client({ host: "127.0.0.1", port }); await right.ready; a = await right.rpc("auth", { token: tok }); const l2 = await right.rpc("tools/list");
  ck("real", "tcp accepts the right token", a.result?.ok && l2.result?.tools?.length === 6, JSON.stringify(l2).slice(0, 200));
  ck("real", "token does not appear in status", !JSON.stringify(ts).includes(tok));
  await right.end(); await t.close();
  const ext = server({ CLAW_LISTEN: "tcp:0.0.0.0:0", CLAW_STATE_DIR: stateDir });
  let es = J(await ext.dev({ action: "platform" }));
  for (let i = 0; i < 50 && es.listener?.state === "not started"; i++) { await sleep(50); es = J(await ext.dev({ action: "platform" })); }
  ck("real", "non-loopback bind is refused", es.listener?.state === "disabled" && /loopback only/.test(es.listener.why), JSON.stringify(es));
  await ext.close();
  const forced = server({ CLAW_PLATFORM: "aesc" });
  r = await forced.dev({ action: "toast", args: ["x"] }); ck("fake", "CLAW_PLATFORM=aesc with no daemon fails clearly, no silent termux", r.err && /no backend serves/.test(r.t), r.t);
  await forced.close();
  if (process.env.REAL_TERMUX_API) {
    const live = server({ STUBPATH: "/nonexistent" });
    r = await live.dev({ action: "battery" }); let pct = -1; try { pct = JSON.parse(r.t).percentage; } catch {}
    ck("real", "battery through the termux backend (real Termux:API)", !r.err && pct >= 0, r.t);
    await live.close();
  } else console.log("UNTESTED [real] Termux:API (termux-battery-status not on PATH)");
}

// ======== 5. ADB
{
  const keyFile = join(T, "adbkey");
  let realKeygen = false;
  try { execFileSync("adb", ["keygen", keyFile], { stdio: "ignore", env: { ...process.env, PATH: process.env.REALPATH } }); realKeygen = existsSync(keyFile + ".pub"); } catch {}
  if (!realKeygen) { const { privateKey } = generateKeyPairSync("rsa", { modulusLength: 2048 }); writeFileSync(keyFile, privateKey.export({ type: "pkcs8", format: "pem" }), { mode: 0o600 }); console.log("UNTESTED [real] adb keygen cross-check (adb binary could not create a key)"); }
  const key = createPrivateKey(readFileSync(keyFile, "utf8")), pub = adbPublicKeyB64(key);
  if (realKeygen) ck("real", "public key encoding matches the real adb binary (adb keygen)", readFileSync(keyFile + ".pub", "utf8").split(" ")[0].trim() === pub);
  ck("fake", "public key blob parses back to the same RSA key", keyFromAdbBlob(pub).export({ type: "spki", format: "der" }).equals(createPublicKey(key).export({ type: "spki", format: "der" })));
  const pem = adbCertificatePem(key), cert = new X509Certificate(pem);
  ck("real", "TLS certificate parses and self-verifies (OpenSSL in Node)", cert.verify(createPublicKey(key)) && new Date(cert.validTo) > new Date());
  try {
    const f = join(T, "c.pem"); writeFileSync(f, pem);
    const o = execFileSync("openssl", ["x509", "-in", f, "-noout", "-subject", "-pubkey"], { encoding: "utf8", env: { ...process.env, PATH: process.env.REALPATH } });
    ck("real", "TLS certificate accepted by the openssl binary", /CN\s*=\s*adb/.test(o) && o.includes("BEGIN PUBLIC KEY"), o);
  } catch (e) { ck("real", "TLS certificate accepted by the openssl binary", false, e.message); }

  const env = { CLAW_ADB_KEY: keyFile, CLAW_ADB_AUTH_WAIT: "400" };
  const other = adbPublicKeyB64(createPrivateKey(generateKeyPairSync("rsa", { modulusLength: 2048 }).privateKey.export({ type: "pkcs8", format: "pem" })));
  // Plain mode, key trusted.
  let f = await fakeAdbd({ trusted: [pub] }); let s = server(env);
  let r = await s.dev({ action: "adb-status" }); ck("fake", "adb-status before connect", J(r).connected === false, r.t);
  r = await s.dev({ action: "adb-connect", port: f.port }); ck("fake", "adb connect: CNXN + AUTH signature accepted, no prompt", J(r).connected === true && J(r).mode === "plain" && f.log.prompted === 0, r.t);
  r = await s.dev({ action: "adb-shell", command: "echo hi" }); ck("fake", "adb shell v2: stdout and exit code", J(r).stdout === "hi\n" && J(r).exit === 0 && f.log.opens.at(-1) === "shell,v2,raw:echo hi", r.t);
  r = await s.dev({ action: "adb-shell", command: "fail" }); ck("fake", "adb shell v2: stderr and nonzero exit", J(r).stderr === "bad\n" && J(r).exit === 3, r.t);
  r = await s.dev({ action: "adb-shell", command: "big" }); ck("fake", "adb shell: 300 KB across split frames, intact", J(r).stdout?.length === 300000, r.t.slice(0, 200));
  r = await s.dev({ action: "adb-tap", x: 12, y: 34 }); ck("fake", "adb tap reaches the device as input tap", r.t === "tapped 12,34" && f.log.taps.at(-1)?.join() === "12,34", r.t);
  r = await s.dev({ action: "adb-tap", x: "1; rm -rf /", y: 2 }); ck("fake", "adb tap rejects non-integers", r.err && !f.log.shells.some((x) => x.includes("rm")), r.t);
  const apk = join(T, "a.apk"), bytes = randomBytes(70000); writeFileSync(apk, bytes);
  r = await s.dev({ action: "adb-install", path: apk });
  const inst = f.log.installs.at(-1);
  ck("fake", "adb install streams every byte in maxdata chunks", J(r).result === "Success" && inst?.sha === createHash("sha256").update(bytes).digest("hex") && inst.packets >= 17 && inst.replace === true, r.t + JSON.stringify(inst));
  r = await s.dev({ action: "adb-install", path: join(T, "none.apk") }); ck("fake", "adb install: missing file errors", r.err && /no APK/.test(r.t), r.t);
  ck("fake", "fake adbd saw no protocol violations (plain)", f.log.errors.length === 0, f.log.errors.join());
  await s.close(); f.close();
  // Install failure text comes back as an error.
  f = await fakeAdbd({ trusted: [pub], installFails: true }); s = server(env);
  r = await s.dev({ action: "adb-install", path: apk, port: f.port }); ck("fake", "adb install: device failure surfaces", r.err && /INSTALL_FAILED_TEST/.test(r.t), r.t);
  await s.close(); f.close();
  // Device without shell_v2.
  f = await fakeAdbd({ trusted: [pub], features: "cmd" }); s = server(env);
  r = await s.dev({ action: "adb-shell", command: "echo hi", port: f.port }); ck("fake", "adb shell without shell_v2 falls back to shell:", J(r).stdout === "hi\n" && f.log.opens.at(-1) === "shell:echo hi", r.t);
  await s.close(); f.close();
  // Unknown key: prompt, operator allows.
  f = await fakeAdbd({ trusted: [other], allowPrompt: true }); s = server(env);
  r = await s.dev({ action: "adb-connect", port: f.port }); ck("fake", "adb unknown key: public key sent once, accepted", J(r).connected === true && f.log.prompted === 1 && f.log.promptKey === pub, r.t);
  await s.close(); f.close();
  // Unknown key: nobody answers the prompt.
  f = await fakeAdbd({ trusted: [other] }); s = server(env);
  r = await s.dev({ action: "adb-connect", port: f.port }); let c = parseChoice(r.t, "claw.device");
  ck("fake", "adb prompt unanswered -> CHOICE", r.err && c?.options[0] === "I allowed it, retry", r.t);
  await s.close(); f.close();
  // Wireless debugging mode: STLS + TLS 1.3. Server cert comes from a throwaway key, using the same writer.
  const srv = createPrivateKey(generateKeyPairSync("rsa", { modulusLength: 2048 }).privateKey.export({ type: "pkcs8", format: "pem" }));
  const tlsOpts = { mode: "tls", serverKey: srv.export({ type: "pkcs8", format: "pem" }), serverCert: adbCertificatePem(srv) };
  f = await fakeAdbd({ trusted: [pub], ...tlsOpts }); s = server(env);
  r = await s.dev({ action: "adb-connect", port: f.port });
  ck("fake", "adb STLS: TLS 1.3 handshake with client cert for the adb key", J(r).mode === "tls" && f.log.tlsClientKeyOk === true && f.log.tlsVersion === "TLSv1.3", r.t + JSON.stringify(f.log));
  r = await s.dev({ action: "adb-shell", command: "echo hi" }); ck("fake", "adb shell over TLS", J(r).stdout === "hi\n", r.t);
  r = await s.dev({ action: "adb-tap", x: 5, y: 6 }); ck("fake", "adb tap over TLS", f.log.taps.at(-1)?.join() === "5,6", r.t);
  r = await s.dev({ action: "adb-install", path: apk }); ck("fake", "adb install over TLS", f.log.installs.at(-1)?.sha === createHash("sha256").update(bytes).digest("hex"), r.t);
  await s.close(); f.close();
  f = await fakeAdbd({ trusted: [other], ...tlsOpts }); s = server(env);
  r = await s.dev({ action: "adb-connect", port: f.port }); ck("fake", "adb STLS: unpaired key is rejected, reported as not reachable", r.err && f.log.tlsClientKeyOk === false && !!parseChoice(r.t, "claw.device"), r.t);
  await s.close(); f.close();
  // Dropped connection reconnects.
  f = await fakeAdbd({ trusted: [pub] }); s = server({ ...env, CLAW_ADB_PORT: String(f.port) });
  r = await s.dev({ action: "adb-shell", command: "echo hi" }); ck("fake", "adb connects on demand (CLAW_ADB_PORT)", J(r).stdout === "hi\n", r.t);
  await s.close(); f.close();
  // Real refusal, real non-adb port, non-loopback.
  s = server(env);
  const closed = await new Promise((res) => { const x = net.createServer().listen(0, "127.0.0.1", () => { const p = x.address().port; x.close(() => res(p)); }); });
  r = await s.dev({ action: "adb-connect", port: closed }); c = parseChoice(r.t, "claw.device");
  ck("real", "adb: nothing listening -> ECONNREFUSED and CHOICE", r.err && /ECONNREFUSED/.test(r.t) && c?.options[0] === "Wireless debugging is on, retry", r.t);
  const notAdb = await new Promise((res) => { const x = net.createServer((k) => { k.on("error", () => {}); k.write("HTTP/1.1 400 Bad Request\r\n\r\nthis is definitely not an adb daemon\r\n"); }).listen(0, "127.0.0.1", () => res(x)); });
  r = await s.dev({ action: "adb-connect", port: notAdb.address().port }); ck("real", "adb: a non-adb service is detected, no hang", r.err && /bad adb packet/.test(r.t), r.t); notAdb.close();
  r = await s.dev({ action: "adb-connect", host: "8.8.8.8", port: 5555 }); ck("real", "adb: non-loopback host refused", r.err && /loopback only/.test(r.t), r.t);
  await s.close();
  s = server({ CLAW_ADB_KEY: join(T, "missing-key") }); r = await s.dev({ action: "adb-connect", port: closed }); ck("real", "adb: missing key explained, nothing created", r.err && /no adb key/.test(r.t) && !existsSync(join(T, "missing-key")), r.t); await s.close();
}

// ======== 6. Crawl
{
  const W = await site(); const s = server();
  let r = await s.scr({ action: "crawl", url: W.url + "/", delay_ms: 1 }), j = J(r);
  const paths = (j.pages || []).map((p) => new URL(p.url).pathname).sort();
  ck("fake", "crawl: same-origin pages within depth 2", paths.join() === "/,/a,/b,/c,/private/ok", paths.join() + " " + r.t.slice(0, 300));
  ck("fake", "crawl: robots Disallow honoured, longer Allow wins", !W.hits.includes("/private/x") && W.hits.includes("/private/ok") && j.skipped?.robots === 1, JSON.stringify(j.skipped));
  ck("fake", "crawl: never left the origin", !W.hits.some((h) => h.startsWith("other:")) && j.skipped.offsite >= 1, W.hits.join());
  ck("fake", "crawl: fragment deduped, /b fetched once", W.hits.filter((h) => h === "/b").length === 1);
  ck("fake", "crawl: nofollow, script, comment, pdf links not fetched", !["/nf", "/fromscript", "/fromcomment", "/f.pdf"].some((x) => W.hits.includes(x)), W.hits.join());
  ck("fake", "crawl: binary content not returned", j.skipped.not_html >= 2 && !paths.includes("/data"), JSON.stringify(j.skipped));
  ck("fake", "crawl: depth limit keeps /d out", !W.hits.includes("/d"));
  ck("fake", "crawl: robots.txt read first, once", W.hits[0] === "/robots.txt" && W.hits.filter((h) => h === "/robots.txt").length === 1, W.hits.slice(0, 3).join());
  ck("fake", "crawl: pages carry markdown", j.pages?.[0].markdown.includes("# Home"), r.t.slice(0, 300));
  const g = W.times.slice(1).map((t, i) => t - W.times[i]);
  ck("fake", "crawl: delay floor 250 ms holds even when asked for 1 ms", g.every((x) => x >= 240), g.join());
  W.hits.length = 0; W.times.length = 0;
  r = await s.scr({ action: "crawl", url: W.url + "/many", max_pages: 3, delay_ms: 300 }); j = J(r);
  ck("fake", "crawl: max_pages stops it and says so", j.pages?.length === 3 && j.stopped === "max_pages" && W.hits.length <= 4, r.t.slice(0, 200));
  const g2 = W.times.slice(1).map((t, i) => t - W.times[i]); ck("fake", "crawl: requested delay respected", g2.every((x) => x >= 290), g2.join());
  r = await s.scr({ action: "crawl", url: W.url + "/many", max_pages: 99999, max_depth: 99, deadline_ms: 700, delay_ms: 250 }); j = J(r);
  ck("fake", "crawl: deadline stops it", j.stopped === "deadline" && j.elapsed_ms < 3000, r.t.slice(0, 200));
  W.hits.length = 0;
  r = await s.scr({ action: "crawl", url: W.url + "/limitstart", delay_ms: 1 }); j = J(r);
  ck("fake", "crawl: HTTP 429 stops the crawl, reports Retry-After", /rate_limited.*Retry-After 120/.test(j.stopped) && !W.hits.includes("/after"), r.t.slice(0, 300));
  W.hits.length = 0;
  r = await s.scr({ action: "crawl", url: W.url + "/redirstart", delay_ms: 1 }); j = J(r);
  ck("fake", "crawl: offsite redirect not followed", !W.hits.some((h) => h === "other:/landed") && j.skipped.offsite === 1, r.t.slice(0, 300) + W.hits.join());
  W.hits.length = 0;
  r = await s.scr({ action: "crawl", url: W.url + "/", same_origin: false, max_depth: 1, delay_ms: 1, include: "^" + W.other.replace(/\./g, "\\.") }); j = J(r);
  ck("fake", "crawl: same_origin=false is opt-in and works", W.hits.some((h) => h === "other:/z"), W.hits.join());
  r = await s.scr({ action: "map", url: W.url + "/", delay_ms: 1, max_depth: 1 }); j = J(r);
  ck("fake", "map: URLs only, no page text", j.urls?.length >= 3 && !r.t.includes("markdown"), r.t.slice(0, 300));
  r = await s.scr({ action: "crawl", url: "file:///etc/hosts" }); ck("fake", "crawl: file:// refused", r.err && /http/.test(r.t), r.t);
  r = await s.scr({ url: W.url + "/inject" });
  ck("fake", "page text cannot raise a card (CHOICE line)", parseChoice(r.t, "claw.scrape") === null && r.t.includes("Evil page question"), r.t);
  r = await s.scr({ url: W.url + "/inject", format: "html" }); ck("fake", "page text cannot raise a card (raw html, JSON form)", parseChoice(r.t, "claw.scrape") === null, r.t);
  const rb = parseRobots("# c\nUser-agent: other\nDisallow: /\n\nUser-agent: claw-mcp\nUser-agent: x\nDisallow: /a*z$\nCrawl-delay: 2\n\nUser-agent: *\nDisallow: /");
  ck("fake", "robots parser: own group chosen, wildcard + anchor, delay", rb.allowed("/") && !rb.allowed("/a1z") && rb.allowed("/a1zy") && rb.delay === 2000);
  await s.close(); W.close();
}

// ======== 7. Video
{
  const W = await site();
  const stub = join(T, "yt-stub.mjs");
  writeFileSync(stub, `import {writeFileSync} from "node:fs"; const a=process.argv.slice(2), url=a.at(-1);
const base={id:"vid1",title:"A Title",uploader:"Up",duration:90,upload_date:"20260101",view_count:5,description:"d",extractor:"stub",webpage_url:url,subtitles:{},automatic_captions:{}};
if(url.includes("blocked")){console.error("ERROR: Sign in to confirm you are not a bot");process.exit(1)}
if(a.includes("--write-subs")||a.includes("--write-auto-subs")){const o=a[a.indexOf("-o")+1];writeFileSync(o+".en.vtt","WEBVTT\\n\\n00:00:09.000 --> 00:00:10.000\\nvia yt-dlp file\\n");process.exit(0)}
if(url.includes("nocap")){} else if(url.includes("forbidden")) base.subtitles={en:[{ext:"vtt",url:"${W.url}/sub-forbidden.vtt"}]};
else if(url.includes("foreign")) base.subtitles={ja:[{ext:"vtt",url:"${W.url}/sub.vtt"}],fr:[{ext:"vtt",url:"${W.url}/sub.vtt"}]};
else if(url.includes("autoen")) base.automatic_captions={"en-orig":[{ext:"json3",url:"${W.url}/sub.json3"}],de:[{ext:"json3",url:"${W.url}/sub-forbidden.vtt"}]};
else base.subtitles={en:[{ext:"srv3",url:"${W.url}/nope"},{ext:"vtt",url:"${W.url}/sub.vtt"}]};
console.log(JSON.stringify(base));`);
  writeFileSync(join(T, "yt-stub"), `#!/bin/sh\nexec node "${stub}" "$@"\n`); chmodSync(join(T, "yt-stub"), 0o755);
  const s = server({ CLAW_YTDLP: join(T, "yt-stub") });
  let r = await s.scr({ action: "video", url: "https://v.test/ok" }), j = J(r);
  ck("fake", "video: metadata + captions via stub yt-dlp", j.metadata?.title === "A Title" && j.via === "yt-dlp" && j.transcript?.kind === "captions" && j.transcript.format === "vtt", r.t);
  ck("fake", "video: VTT cleaned, rolling repeats dropped, timestamps", j.transcript?.text === "[0:01] Hello there\n[0:03] second line\n[1:02:03] the & end", j.transcript?.text);
  r = await s.scr({ action: "video", url: "https://v.test/ok", timestamps: false }); ck("fake", "video: timestamps off", J(r).transcript?.text.startsWith("Hello there\n"), r.t);
  r = await s.scr({ action: "video", url: "https://v.test/ok", metadata_only: true }); ck("fake", "video: metadata_only", J(r).transcript === undefined && J(r).metadata?.id === "vid1", r.t);
  r = await s.scr({ action: "video", url: "https://v.test/autoen" }); j = J(r); ck("fake", "video: auto captions, en-orig, json3", j.transcript?.lang === "en-orig" && j.transcript.kind === "auto" && j.transcript.text === "[0:01] From json3\n[1:06] minute one", r.t);
  r = await s.scr({ action: "video", url: "https://v.test/foreign" }); let c = parseChoice(r.t, "claw.scrape");
  ck("fake", "video: no English -> CHOICE of languages", c?.options.join() === "ja,fr" && J(r).transcript === null, r.t);
  r = await s.scr({ action: "video", url: "https://v.test/foreign", lang: "fr" }); ck("fake", "video: lang picks the track", J(r).transcript?.lang === "fr", r.t);
  r = await s.scr({ action: "video", url: "https://v.test/foreign", lang: "de" }); ck("fake", "video: missing lang says so, no fabrication", J(r).transcript === null && /no captions in .*de/.test(r.t), r.t);
  r = await s.scr({ action: "video", url: "https://v.test/nocap" }); ck("fake", "video: no captions -> metadata, transcript null, says why", J(r).transcript === null && J(r).metadata?.title === "A Title" && /speech-to-text is not available/.test(r.t), r.t);
  r = await s.scr({ action: "video", url: "https://v.test/forbidden" }); ck("fake", "video: caption URL refused -> yt-dlp fetches the file", J(r).transcript?.text === "[0:09] via yt-dlp file", r.t);
  r = await s.scr({ action: "video", url: W.url + "/blocked" }); ck("fake", "video: yt-dlp blocked and no page data -> clear error", r.err && /not a bot/.test(r.t), r.t);
  await s.close();
  const n = server({ CLAW_YTDLP: join(T, "does-not-exist") });
  r = await n.scr({ action: "video", url: W.url + "/watch-yt" }); j = J(r);
  ck("fake", "video: without yt-dlp, YouTube player JSON from the page", j.via === "page" && j.metadata?.title === "Page } Title" && j.metadata.duration === 42 && j.transcript?.text === "[0:00] page fallback caption", r.t);
  r = await n.scr({ action: "video", url: W.url + "/generic-video" }); j = J(r);
  ck("fake", "video: without yt-dlp, og: tags + <track> from any page", j.metadata?.title === "Generic & Title" && j.transcript?.format === "vtt", r.t);
  r = await n.scr({ action: "video", url: W.url + "/no-video" }); ck("fake", "video: page with nothing errors", r.err && /no video data/.test(r.t), r.t);
  await n.close(); W.close();
  ck("fake", "VTT parser ignores header and notes", parseVtt("WEBVTT\n\nNOTE hi\n\n00:01.000 --> 00:02.000\nshort stamp\n")[0]?.text === "short stamp");
}

// ======== 8. Google
{
  const G = await fakeGoogle(), dir = join(T, "google"); mkdirSync(dir, { mode: 0o700 });
  const put = (name, o, mode = 0o600) => { const f = join(dir, `google-${name}.json`); writeFileSync(f, JSON.stringify(o), { mode }); chmodSync(f, mode); return f; };
  put("work", GOOGLE);
  const env = { CLAW_GOOGLE_DIR: dir, CLAW_GOOGLE_BASE: G.url }; const s = server(env), g = (a) => s.dev({ action: "google", ...a });
  let r = await g({ service: "drive", query: "name contains 'x'" }), j = J(r);
  ck("fake", "google: refresh token -> access token -> Drive list", j.files?.length === 2 && j.echo_q === "name contains 'x'" && j.echo_all === "true" && G.log.refreshes === 1, r.t);
  r = await g({ service: "drive", id: "txt1" }); ck("fake", "google: access token cached between calls", J(r).content === "plain file text" && G.log.refreshes === 1, r.t);
  r = await g({ service: "drive", id: "doc1" }); j = J(r); ck("fake", "google: Doc exports, falls back when markdown is refused", j.exported_as === "text/plain" && j.content === "doc as text", r.t);
  r = await g({ service: "drive", id: "sheet1" }); ck("fake", "google: Sheet exports as CSV", J(r).content === "a,b\n1,2\n", r.t);
  r = await g({ service: "drive", id: "bin1" }); ck("fake", "google: binary not printed", J(r).content === null, r.t);
  r = await g({ service: "drive", id: "form1" }); ck("fake", "google: non-exportable type says so", J(r).content === null && /no text export/.test(r.t), r.t);
  r = await g({ service: "drive", op: "get", id: "txt1" }); ck("fake", "google: Drive get is metadata only", J(r).name === "t.txt" && J(r).content === undefined, r.t);
  r = await g({ service: "drive", id: "missing" }); ck("fake", "google: API error surfaces", r.err && /HTTP 404/.test(r.t), r.t);
  const before = G.log.refreshes;
  r = await g({ service: "drive", op: "get", id: "revoked" }); ck("fake", "google: 401 forces one refresh and retry", J(r).id === "revoked" && G.log.refreshes === before + 1, r.t);
  r = await g({ service: "gmail", query: "from:a" }); j = J(r); ck("fake", "google: Gmail list carries headers", j.messages?.[0].subject === "Hi" && j.messages[0].from === "a@b.c" && j.messages[0].snippet === "snip", r.t);
  r = await g({ service: "gmail", id: "m1" }); j = J(r); ck("fake", "google: Gmail get decodes nested text/plain, lists attachments", j.body === "plain body é" && j.attachments?.[0] === "a.pdf", r.t);
  r = await g({ service: "gmail", id: "h1" }); ck("fake", "google: Gmail html-only body becomes Markdown", J(r).body === "# only html", r.t);
  r = await g({ service: "gmail", op: "thread", id: "t1" }); ck("fake", "google: Gmail thread", J(r).messages?.length === 2, r.t);
  r = await g({ service: "gmail", op: "labels" }); ck("fake", "google: Gmail labels", J(r).labels?.[0].id === "INBOX", r.t);
  r = await g({ service: "calendar" }); j = J(r); ck("fake", "google: Calendar list asks for ordered, expanded events", j.items?.[0].summary === "Standup" && j.echo.singleEvents === "true" && j.echo.orderBy === "startTime" && !!j.echo.timeMin, r.t);
  r = await g({ service: "calendar", id: "e1" }); ck("fake", "google: Calendar get", J(r).id === "e1", r.t);
  r = await g({ service: "calendar", op: "calendars" }); ck("fake", "google: Calendar calendars", J(r).items?.[0].id === "primary", r.t);
  // Writes wait for a pick.
  r = await g({ service: "calendar", op: "create", summary: "Lunch", start: "2026-12-01T12:00:00Z", end: "2026-12-01T13:00:00Z" }); let c = parseChoice(r.t, "claw.device");
  ck("fake", "google: Calendar create without confirm -> CHOICE, nothing posted", c?.options[0] === "Create it" && G.log.posts.length === 0, r.t);
  r = await g({ service: "calendar", op: "create", summary: "Lunch", start: "2026-12-01", end: "2026-12-02", confirm: true }); let post = G.log.posts.at(-1);
  ck("fake", "google: Calendar create with confirm, no invitations", JSON.parse(post.body).start.date === "2026-12-01" && post.search === "?sendUpdates=none", JSON.stringify(post));
  r = await g({ service: "gmail", op: "draft", to: "a@b.c", subject: "Sé", body: "hello" }); ck("fake", "google: Gmail draft without confirm -> CHOICE", !!parseChoice(r.t, "claw.device") && G.log.posts.length === 1, r.t);
  r = await g({ service: "gmail", op: "draft", to: "a@b.c", subject: "x\r\nBcc: evil@e.vil", body: "hello", confirm: true }); ck("fake", "google: header injection in a draft refused", r.err && G.log.posts.length === 1, r.t);
  r = await g({ service: "gmail", op: "draft", to: "a@b.c", subject: "Sé", body: "hello", confirm: true }); post = G.log.posts.at(-1);
  const mime = Buffer.from(JSON.parse(post.body).message.raw, "base64url").toString();
  ck("fake", "google: Gmail draft MIME is correct and uses drafts, not send", post.p.endsWith("/drafts") && mime.includes("To: a@b.c\r\n") && mime.includes(`=?UTF-8?B?${Buffer.from("Sé").toString("base64")}?=`) && mime.endsWith("\r\n\r\nhello"), mime);
  r = await g({ service: "drive", op: "create", name: "n.txt", content: "body text", confirm: true }); post = G.log.posts.at(-1);
  ck("fake", "google: Drive create multipart", J(r).id === "new1" && /multipart\/related/.test(post.type) && post.body.includes("body text") && post.body.includes('"name":"n.txt"'), JSON.stringify(post));
  ck("fake", "google: nothing ever called send, delete or share", !G.log.paths.some((p) => /\/send|^DELETE|permissions/.test(p)), G.log.paths.join());
  // Secrets.
  r = await g({ service: "drive", op: "get", id: "leaky" });
  ck("fake", "google: a server echoing tokens is redacted", r.err && r.t.includes("[redacted]") && !r.t.includes(GOOGLE.refresh_token) && !r.t.includes(GOOGLE.client_secret) && !/ya29\./.test(r.t), r.t);
  // Bad inputs.
  r = await g({ service: "drive", account: "../../etc/x" }); ck("fake", "google: path traversal in account refused", r.err && /bad account name/.test(r.t), r.t);
  put("loose", GOOGLE, 0o644); r = await g({ service: "drive", account: "loose" }); ck("real", "google: world-readable token file refused", r.err && /chmod 600/.test(r.t), r.t);
  r = await g({ service: "drive" }); c = parseChoice(r.t, "claw.device"); ck("fake", "google: two accounts and none named -> CHOICE", r.err && c?.options.join() === "loose,work", r.t);
  put("stale", { ...GOOGLE, refresh_token: "1//wrong-refresh-token-FAKE-00000000" }); r = await g({ service: "drive", account: "stale" });
  ck("fake", "google: invalid_grant explained, token not echoed", r.err && /expired or revoked/.test(r.t) && !r.t.includes("wrong-refresh"), r.t);
  put("at", { access_token: "ya29.static-FAKE-access" }); r = await g({ service: "drive", account: "at" }); ck("fake", "google: bare access_token file works", J(r).files?.length === 2, r.t);
  put("old", { access_token: "ya29.static-FAKE-access", expiry: "2020-01-01T00:00:00Z" }); r = await g({ service: "drive", account: "old" }); ck("fake", "google: expired access_token refused clearly", r.err && /expired/.test(r.t) && !r.t.includes("static-FAKE"), r.t);
  await s.close();
  const evil = server({ CLAW_GOOGLE_DIR: dir, CLAW_GOOGLE_BASE: "https://evil.test" });
  const hits = G.log.refreshes; r = await evil.dev({ action: "google", service: "drive", account: "work" }); ck("fake", "google: base override only to loopback, so tokens cannot be redirected", r.err && /127\.0\.0\.1/.test(r.t) && G.log.refreshes === hits, r.t);
  await evil.close(); G.close();
  const dump = everything.join("");
  const leaked = [GOOGLE.refresh_token, GOOGLE.client_secret, "ya29.fake-access", "ya29.static-FAKE", "wrong-refresh-token"].filter((x) => dump.includes(x));
  ck("fake", `no token in any output of this run (${dump.length} bytes scanned)`, leaked.length === 0, leaked.join());
}

process.exit(bad);
