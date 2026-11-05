// Platform layer: one interface, two backends, picked at runtime per call.
//   backend = { name, available(), has(op), call(op, args) -> Promise<string|object> }
//   termux: Termux:API binaries on PATH.
//   aesc:   the Aesc daemon, when it has connected to claw's socket (listener.mjs) and registered the ops it serves,
//           including "exec:<tool>" for outside tools. When Termux is gone, Aesc registers these and nothing else changes.
// CLAW_PLATFORM=termux|aesc forces one; default auto prefers aesc for the ops it registered, then termux.
import { execFile } from "node:child_process";
import { existsSync } from "node:fs";
import { join } from "node:path";

// Outside tools (adb, rclone, yt-dlp, getprop): Aesc serves any it registered as "exec:<name>"; else run here.
export const run = (cmd, args, ms = 20000) => {
  const name = String(cmd).split("/").pop();
  if (peer && process.env.CLAW_PLATFORM !== "termux" && peer.ops.includes("exec:" + name)) return peer.request("device/exec", { cmd: name, args, ms });
  return runLocal(cmd, args, ms);
};
const runLocal = (cmd, args, ms) => new Promise((res, rej) => {
  const c = execFile(cmd, args, { timeout: ms, maxBuffer: 16 * 1024 * 1024 }, (e, o, er) => {
    if (e && e.code === "ENOENT") return rej(new Error(`${cmd} not installed`));
    if (e && e.killed) return rej(new Error(`${cmd} timed out after ${ms} ms`));
    if (e && e.code === "ERR_CHILD_PROCESS_STDIO_MAXBUFFER") return rej(new Error(`${cmd} output exceeded 16 MB`));
    const text = (o + er).trim();
    if (e) return rej(new Error(`${cmd} exit ${e.code}${text ? ": " + text.slice(0, 2000) : ""}`));
    res(text || "ok");
  });
  c.stdin?.end(); // termux-toast and friends read stdin when given no argument
});

const TERMUX = {
  battery: () => ["termux-battery-status"],
  wifi: () => ["termux-wifi-connectioninfo"],
  location: () => ["termux-location"],
  "clipboard-get": () => ["termux-clipboard-get"],
  "clipboard-set": (s) => ["termux-clipboard-set", ...s],
  toast: (s) => ["termux-toast", ...s],
  tts: (s) => ["termux-tts-speak", ...s],
  vibrate: (s) => ["termux-vibrate", ...s],
  notify: (s) => ["termux-notification", "-t", s[0] || "claw", "-c", s[1] || ""],
  "open-url": (s) => ["termux-open-url", ...s],
};
export const OPS = Object.keys(TERMUX);
const onPath = (bin) => (process.env.PATH || "").split(":").some((d) => d && existsSync(join(d, bin)));

export const termux = {
  name: "termux",
  available: () => OPS.some((op) => onPath(TERMUX[op]([])[0])),
  has: (op) => !!TERMUX[op] && onPath(TERMUX[op]([])[0]),
  call: (op, args) => { const [cmd, ...rest] = TERMUX[op](args); return run(cmd, rest, op === "location" ? 60000 : 20000); },
};

let peer = null; // { name, ops, request(method, params) }, set by the listener
export const setPeer = (p) => { peer = p; };
export const clearPeer = (p) => { if (peer === p) peer = null; };
export const aesc = {
  name: "aesc",
  available: () => !!peer,
  has: (op) => !!peer && peer.ops.includes(op),
  call: (op, args) => peer.request("device/call", { op, args }),
};

export function select(op) {
  const want = process.env.CLAW_PLATFORM || "auto";
  const order = want === "termux" ? [termux] : want === "aesc" ? [aesc] : want === "auto" ? [aesc, termux] : null;
  if (!order) throw new Error(`CLAW_PLATFORM must be termux|aesc|auto, got ${want}`);
  const b = order.find((x) => x.has(op));
  if (b) return b;
  throw new Error(`no backend serves "${op}" (CLAW_PLATFORM=${want}; termux: ${termux.available() ? "present, missing this command" : "no Termux:API commands on PATH"}; aesc: ${peer ? "connected, op not registered" : "not connected"})`);
}

export const platformStatus = () => ({
  mode: process.env.CLAW_PLATFORM || "auto",
  termux: termux.available(),
  aesc: peer ? { connected: true, name: peer.name, ops: peer.ops } : { connected: false },
  ops: Object.fromEntries(OPS.map((op) => { try { return [op, select(op).name]; } catch { return [op, null]; } })),
});
