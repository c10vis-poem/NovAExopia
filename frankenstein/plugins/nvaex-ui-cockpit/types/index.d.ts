export type Snap = { ctxPct: number | null; ctxWin: number; limits: { kind: string; pct: number; resetsAt?: string }[] }

declare module 'claude-code' {
  interface PluginState {
    'nvaex-ui-cockpit': {
      gauge: Snap
      lastHit: number | null
    }
  }
}
