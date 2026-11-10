// Result wire format shared by every tool: CHOICE lines (nvaex-ui-cockpit hooks/lib/cards.ts), page-text defusing, secret redaction.
const secrets = new Set();
export const addSecret = (v) => { if (typeof v === "string" && v.length >= 8) secrets.add(v); };

export function redact(s) {
  let out = String(s);
  for (const v of secrets) out = out.split(v).join("[redacted]");
  return out
    .replace(/\bBearer\s+[\w.~+/=-]+/gi, "Bearer [redacted]")
    .replace(/\bya29\.[\w.-]+/g, "[redacted]")
    .replace(/\b1\/\/[\w-]{20,}/g, "[redacted]")
    .replace(/("(?:access_token|refresh_token|client_secret|id_token)"\s*:\s*")[^"]*"/g, '$1[redacted]"');
}

// An error the operator can resolve: the message plus a pick.
export class ClawError extends Error { constructor(message, choice) { super(message); this.choice = choice; } }
export const pick = (text, question, options) => ({ text, choice: { question, options } });

const clean = (s) => String(s).replace(/[|\r\n]+/g, " ").replace(/\s+/g, " ").trim();
export function choiceLine({ question, options }) {
  const q = clean(question), o = options.map(clean).filter(Boolean).slice(0, 8);
  return q && o.length ? "CHOICE: " + [q, ...o].join(" | ") : "";
}

// cards.ts scans the whole result text, so a web page could otherwise raise a card by printing either wire form.
// Only a line claw itself appends may match its parser. U+200B keeps the text readable.
export const defuse = (text) => String(text).replace(/^CHOICE:/gm, "CHOICE​:").replace(/(\{\s*)"choice"(\s*:\s*\{)/g, '$1"choice​"$2');

export function render(r) {
  if (r && typeof r === "object" && r.choice) {
    const line = choiceLine(r.choice), body = defuse(r.text ?? "");
    return body && line ? body + "\n" + line : body || line;
  }
  return defuse(typeof r === "string" ? r : r === undefined ? "" : typeof r === "object" ? JSON.stringify(r) : String(r));
}
export const renderError = (e) => render({ text: e.message, choice: e.choice });
