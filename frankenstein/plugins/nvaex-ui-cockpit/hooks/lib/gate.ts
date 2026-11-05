// Kill switch + python runner. Each mod asks isOff() before acting; an off mod falls through to next(e).
import type { EngineInterface } from 'claude-code'

export const PKG = 'nvaex-ui-cockpit'
const seen = new Map<string, { at: number; off: boolean }>()

// scripts/killswitch.sh exits 0 = off. Cached 2s so a redraw never spawns a process. Fails open.
export async function isOff($: EngineInterface, mod: string): Promise<boolean> {
  const now = await $.clock.now()
  const hit = seen.get(mod)
  if (hit && now - hit.at < 2000) return hit.off
  let off = false
  try {
    off = (await $.process.run(['sh', `${$.plugin.root}/scripts/killswitch.sh`, PKG, mod])).exitCode === 0
  } catch {}
  seen.set(mod, { at: now, off })
  return off
}

export async function py($: EngineInterface, script: string, args: string[] = []): Promise<string> {
  try {
    const r = await $.process.run(['python3', `${$.plugin.root}/scripts/${script}`, ...args], { timeoutMs: 15000 })
    return (r.exitCode === 0 ? r.stdout : r.stderr || r.stdout).trimEnd()
  } catch (err) {
    return `${script} failed: ${String(err)}`
  }
}
