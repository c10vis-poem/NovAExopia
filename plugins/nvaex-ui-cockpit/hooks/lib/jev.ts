// Pure: what the Jev panel shows. Reads only data other code wrote; says plainly when it is absent.
export type Decision = { decision: string; status?: string; rejected?: string[] }

export const jsonl = (t: string): any[] => t.split('\n').flatMap(l => { try { return l.trim() ? [JSON.parse(l)] : [] } catch { return [] } })

// "JEV route: L2 | groups a/b | try x, y" is the line nvaex-jev-core's router injects into the prompt context.
export function latestRoute(texts: string[]): string | null {
  for (let i = texts.length - 1; i >= 0; i--) {
    const m = /JEV route: (L\d)([^\n]*)/.exec(texts[i])
    if (m) return `${m[1]}${m[2]}`.trim()
  }
  return null
}

export function view(o: { route: string | null; decisions: string | null; scorecard: string | null }): string[] {
  const out: string[] = []
  out.push(o.route ? `Routing tier: ${o.route}` : 'Routing tier: not found (no "JEV route:" line in this conversation; nvaex-jev-core absent, off, or the prompt matched nothing).')
  if (o.decisions === null) out.push('Decisions: file not found (~/.nvaex/decisions.jsonl and <project>/.nvaex/decisions.jsonl).')
  else {
    const d = jsonl(o.decisions).filter((x): x is Decision => x && typeof x.decision === 'string' && (x.status ?? 'active') === 'active')
    out.push(`Recent decisions (${d.length} active):`)
    for (const x of d.slice(-8).reverse()) out.push(`  ${x.decision}${x.rejected?.length ? ` (not ${x.rejected.slice(0, 3).join(', ')})` : ''}`)
    if (!d.length) out.push('  none active')
  }
  if (o.scorecard === null) out.push('Scorecard: file not found (~/.claude/state/nvaex-jev-core/scorecard.jsonl).')
  else {
    const s = jsonl(o.scorecard).slice(-1)[0]
    out.push(s ? `Last scorecard: ${JSON.stringify(s).slice(0, 160)}` : 'Scorecard: file empty')
  }
  return out
}

// Every text block of the conversation, so latestRoute can find the router's injected line.
export function textsOf(messages: any[]): string[] {
  const out: string[] = []
  for (const m of messages ?? []) {
    if (typeof m?.content === 'string') out.push(m.content)
    else for (const b of m?.content ?? []) if (typeof b?.text === 'string') out.push(b.text)
  }
  return out
}
