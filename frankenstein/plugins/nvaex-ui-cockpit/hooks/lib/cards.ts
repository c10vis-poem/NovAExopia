// Pure: browser choice cards. A card is a question with options that an agent driving a browser needs answered.
export type Card = { id: string; question: string; options: string[]; tool: string }

export const isBrowserTool = (t: string) => /browser|chrome|playwright|claw|tinyfish|webview|puppeteer|cdp/i.test(t)

const hash = (s: string) => { let h = 5381; for (const c of s) h = ((h << 5) + h + c.charCodeAt(0)) | 0; return (h >>> 0).toString(36) }

// Two wire forms a tool result may carry:  CHOICE: question | opt | opt   or a JSON {"choice":{"question":"..","options":[..]}}
export function parseChoice(text: string, tool: string): Card | null {
  const m = /^CHOICE:\s*(.+)$/m.exec(text)
  if (m) {
    const [q, ...opts] = m[1].split('|').map(s => s.trim()).filter(Boolean)
    return q && opts.length ? { id: hash(q + opts.join('|')), question: q, options: opts.slice(0, 8), tool } : null
  }
  const j = /\{\s*"choice"\s*:\s*\{[\s\S]*?\}\s*\}/.exec(text)
  if (j) {
    try {
      const c = JSON.parse(j[0]).choice
      if (typeof c?.question === 'string' && Array.isArray(c.options) && c.options.length)
        return { id: hash(c.question + c.options.join('|')), question: c.question, options: c.options.map(String).slice(0, 8), tool }
    } catch {}
  }
  return null
}

export const textOf = (r: unknown): string =>
  typeof r === 'string' ? r : r == null ? '' : typeof r === 'object' ? JSON.stringify(r) : String(r)

export const push = (cards: Card[], c: Card, max = 5) => (cards.some(x => x.id === c.id) ? cards : [...cards, c].slice(-max))
export const drop = (cards: Card[], id: string) => cards.filter(x => x.id !== id)
export const reply = (c: Card, answer: string) => `Browser choice "${c.question}": ${answer}`
