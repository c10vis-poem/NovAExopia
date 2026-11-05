// Pure: parse scripts/agentconfigs.py output, cycle through workflows and agent packages, build the apply command.
export type Item = { kind: 'market' | 'pkg' | 'wf'; name: string; state: string; detail: string }

export function parse(tsv: string): Item[] {
  const out: Item[] = []
  for (const l of tsv.split('\n')) {
    const [kind, name, state, detail = ''] = l.split('\t')
    if ((kind === 'market' || kind === 'pkg' || kind === 'wf') && name) out.push({ kind, name, state: state ?? '', detail })
  }
  return out
}

// The ring the cycle buttons walk: workflows first, then agent packages that ship agents or are ours.
export const ring = (items: Item[]) => [...items.filter(i => i.kind === 'wf'), ...items.filter(i => i.kind === 'pkg')]

export function step(r: Item[], cur: string, dir: 1 | -1): string {
  if (!r.length) return ''
  const i = r.findIndex(x => key(x) === cur)
  return key(r[i < 0 ? (dir > 0 ? 0 : r.length - 1) : (i + dir + r.length) % r.length])
}
export const key = (i: Item) => `${i.kind}:${i.name}`

const SAFE = /^[A-Za-z0-9][A-Za-z0-9._-]{0,63}(@[A-Za-z0-9][A-Za-z0-9._-]{0,63})?$/

// argv to run for "apply": a workflow selects a harness-scope profile; a package toggles via the claude CLI. Never a shell string.
export function applyArgv(i: Item, repo: string, scripts: string): string[] | null {
  if (!SAFE.test(i.name)) return null
  if (i.kind === 'wf') return ['python3', `${scripts}/profiles.py`, 'use', i.name, '--repo', repo]
  if (i.kind === 'pkg') return ['claude', 'plugin', i.state === 'on' ? 'disable' : 'enable', i.name]
  return null
}
