// Pure formatting for token-cache-gauge. No engine access, so node can test it.
export type Lim = { kind: string; pct: number; resetsAt?: string }

const NAMES: Record<string, string> = { five_hour: '5h', seven_day: '7d', spend_limit: 'spend' }

export function bar(pct: number, width = 8): string {
  const full = Math.round((Math.min(100, Math.max(0, pct)) / 100) * width)
  return '█'.repeat(full) + '░'.repeat(width - full)
}

// 300000 -> "5:00", 0 or less -> "0:00"
export function clock(ms: number): string {
  const s = Math.max(0, Math.ceil(ms / 1000))
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}

export function ttlColor(leftMs: number, ttlMs: number): 'green' | 'yellow' | 'red' {
  const f = leftMs / ttlMs
  return f > 0.4 ? 'green' : f > 0.2 ? 'yellow' : 'red'
}

// Fuel: what is left in a window, like a car's gauge.
export function fuel(l: Lim): { name: string; left: number } {
  return { name: NAMES[l.kind] ?? l.kind, left: Math.max(0, Math.round(100 - l.pct)) }
}

export function fuelColor(left: number): 'green' | 'yellow' | 'red' {
  return left >= 50 ? 'green' : left >= 20 ? 'yellow' : 'red'
}

export function plain(ctxPct: number | null, leftMs: number | null, lims: readonly Lim[]): string {
  const parts = [ctxPct == null ? 'ctx --' : `ctx ${bar(ctxPct, 6)} ${Math.round(ctxPct)}%`]
  parts.push(leftMs == null ? 'cache --:--' : `cache ${clock(leftMs)}`)
  for (const l of lims) {
    const f = fuel(l)
    parts.push(`${f.name} ${f.left}% left`)
  }
  return parts.join(' · ')
}
