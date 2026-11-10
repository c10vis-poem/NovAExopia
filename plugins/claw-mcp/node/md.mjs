// HTML -> Markdown, no deps. Handles headings, links, lists, code, quotes, images, tables as rows.
const SKIP = /<(script|style|noscript|svg|head|template)\b[\s\S]*?<\/\1>/gi;
const ENT = { amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", nbsp: " " };
const dec = (s) => s.replace(/&(#x?[0-9a-f]+|\w+);/gi, (m, e) =>
  e[0] === "#" ? String.fromCodePoint(e[1].toLowerCase() === "x" ? parseInt(e.slice(2), 16) : +e.slice(1)) : ENT[e.toLowerCase()] ?? m);
const attr = (t, n) => (t.match(new RegExp(`\\b${n}\\s*=\\s*("([^"]*)"|'([^']*)'|([^\\s>]+))`, "i")) || []).slice(2).find((x) => x !== undefined);

export function toMarkdown(html) {
  const body = (html.match(/<body\b[\s\S]*<\/body>/i) || [html])[0].replace(/<!--[\s\S]*?-->/g, "").replace(SKIP, "");
  let out = "", pre = 0, hrefs = [], lists = [];
  for (const tok of body.match(/<[^>]+>|[^<]+/g) || []) {
    if (tok[0] !== "<") { out += pre ? dec(tok) : dec(tok).replace(/\s+/g, " "); continue; }
    const m = tok.match(/^<(\/?)([a-z0-9]+)/i); if (!m) continue;
    const close = !!m[1], t = m[2].toLowerCase();
    if (/^h[1-6]$/.test(t)) out += close ? "\n\n" : "\n\n" + "#".repeat(+t[1]) + " ";
    else if (t === "p" || t === "div" || t === "section" || t === "article" || t === "tr" || t === "table") out += "\n\n";
    else if (t === "br") out += "\n";
    else if (t === "hr") out += "\n\n---\n\n";
    else if (t === "b" || t === "strong") out += "**";
    else if (t === "i" || t === "em") out += "_";
    else if (t === "code" && !pre) out += "`";
    else if (t === "pre") { pre += close ? -1 : 1; out += close ? "\n```\n\n" : "\n\n```\n"; }
    else if (t === "blockquote") out += close ? "\n\n" : "\n\n> ";
    else if (t === "ul" || t === "ol") { close ? lists.pop() : lists.push({ o: t === "ol", n: 0 }); out += "\n"; }
    else if (t === "li" && !close) { const l = lists.at(-1) || { n: 0 }; l.n++; out += "\n" + "  ".repeat(Math.max(0, lists.length - 1)) + (l.o ? l.n + ". " : "- "); }
    else if ((t === "td" || t === "th") && close) out += " | ";
    else if (t === "a") { if (close) { const h = hrefs.pop(); out += h ? `](${h})` : ""; } else { const h = attr(tok, "href"); hrefs.push(h && !h.startsWith("javascript:") ? h : null); if (hrefs.at(-1)) out += "["; } }
    else if (t === "img" && !close) { const s = attr(tok, "src"); if (s) out += `![${dec(attr(tok, "alt") || "")}](${s})`; }
  }
  return out.replace(/[ \t]+\n/g, "\n").replace(/\n{3,}/g, "\n\n").trim();
}
