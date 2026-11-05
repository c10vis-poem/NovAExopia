// Pure: flatten a lazily-listed directory tree into display rows. Dirs first, then name; noise dirs skipped.
export type Ent = { name: string; kind: 'file' | 'dir' | 'other'; size?: number }
export type TreeRow = { path: string; name: string; depth: number; kind: Ent['kind']; open: boolean }

export const SKIP = new Set(['.git', 'node_modules', '__pycache__', '.cache', '.gradle'])
export const join = (a: string, b: string) => (a.endsWith('/') ? a + b : `${a}/${b}`)

export function rowsOf(root: string, cache: Map<string, Ent[]>, open: Set<string>, max = 400): TreeRow[] {
  const out: TreeRow[] = []
  const walk = (dir: string, depth: number) => {
    const ents = [...(cache.get(dir) ?? [])]
      .filter(x => !SKIP.has(x.name))
      .sort((a, b) => (a.kind === 'dir' ? 0 : 1) - (b.kind === 'dir' ? 0 : 1) || a.name.localeCompare(b.name))
    for (const x of ents) {
      if (out.length >= max) return
      const p = join(dir, x.name)
      const isOpen = x.kind === 'dir' && open.has(p)
      out.push({ path: p, name: x.name, depth, kind: x.kind, open: isOpen })
      if (isOpen) walk(p, depth + 1)
    }
  }
  walk(root, 0)
  return out
}

export const label = (r: TreeRow) => `${'  '.repeat(r.depth)}${r.kind === 'dir' ? (r.open ? 'v ' : '> ') : '  '}${r.name}${r.kind === 'dir' ? '/' : ''}`
