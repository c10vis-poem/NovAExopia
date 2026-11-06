// Pure: turn API messages into "what entered context" rows with chars/4 token estimates. Idea from context-window (MIT).
export type Row = { kind: string; name: string; tokens: number }
type Block = { type?: string; text?: string; name?: string; input?: unknown; content?: unknown; thinking?: string }

const size = (v: unknown): number => (v == null ? 0 : typeof v === 'string' ? v.length : JSON.stringify(v).length)
const est = (n: number) => Math.ceil(n / 4)

export function rows(messages: { role: string; content: string | Block[] }[]): Row[] {
  const out: Row[] = []
  const names = new Map<string, string>()
  for (const m of messages) {
    if (typeof m.content === 'string') { out.push({ kind: m.role, name: m.role, tokens: est(m.content.length) }); continue }
    for (const b of m.content ?? []) {
      if (b.type === 'text') out.push({ kind: m.role, name: m.role, tokens: est(size(b.text)) })
      else if (b.type === 'thinking') out.push({ kind: 'thinking', name: 'thinking', tokens: est(size(b.thinking)) })
      else if (b.type === 'tool_use') { names.set(String((b as any).id), String(b.name)); out.push({ kind: 'tool_use', name: String(b.name), tokens: est(size(b.input)) }) }
      else if (b.type === 'tool_result') { const n = names.get(String((b as any).tool_use_id)) ?? 'tool'; out.push({ kind: 'tool_result', name: n, tokens: est(size(b.content)) }) }
    }
  }
  return out
}

// Group by kind+name, biggest first.
export function lines(rs: Row[], top = 20): string[] {
  const g = new Map<string, { n: number; t: number }>()
  for (const r of rs) { const k = `${r.kind}:${r.name}`; const v = g.get(k) ?? { n: 0, t: 0 }; v.n++; v.t += r.tokens; g.set(k, v) }
  return [...g].sort((a, b) => b[1].t - a[1].t).slice(0, top).map(([k, v]) => `${k}  x${v.n}  ~${v.t} tok`)
}
