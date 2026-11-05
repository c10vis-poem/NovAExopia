// Mod 4. One band above the prompt: context fill %, prompt-cache TTL countdown, 5h/7d fuel.
// Adapted from context-bar (session.measure), cache-ttl-timer (turn.step restart) and gas-gauge (fuel look).
// Swap it out alone: touch ~/.claude/state/off/nvaex-ui-cockpit.token-cache-gauge
import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'
import type { Snap } from '../../types'
import { isOff } from '../lib/gate'
import { bar, clock, fuel, fuelColor, plain, ttlColor } from '../lib/gauge-fmt'

const MOD = 'token-cache-gauge'
const snap = atom({ plugin: 'nvaex-ui-cockpit', key: 'gauge' } as const, { ctxPct: null, ctxWin: 0, limits: [] } as Snap)
const lastHit = atom({ plugin: 'nvaex-ui-cockpit', key: 'lastHit' } as const, null as number | null)
const TTL = { '5m': 300_000, '1h': 3_600_000 }

export async function init($: EngineInterface) {
  await $.command.register({ name: 'gauge', description: 'Show context %, cache countdown and 5h/7d fuel. /gauge 5m|1h sets the cache TTL.' })
  if (await isOff($, MOD)) return
  const u = await $.session.usage()
  await update($, snap, () => ({
    ctxPct: u.context.percent ?? null,
    ctxWin: u.context.window,
    limits: u.rateLimits.map(l => ({ kind: l.kind, pct: l.percentUsed, resetsAt: l.resetsAt })),
  }))
  // 1s tick redraws the countdown
  $.clock.every(1000, async () => {
    if (!(await isOff($, MOD))) $.ui.invalidate('ui.render')
  })
}

export const mount = (on: Parameters<Register>[0], options: Parameters<Register>[1]) => {
  let ttl: '5m' | '1h' = options.cacheTtl === '1h' ? '1h' : '5m'

  on('session.measure', async ($, e, next) => {
    if (!(await isOff($, MOD))) {
      await update($, snap, () => ({
        ctxPct: e.context.percent ?? null,
        ctxWin: e.context.window,
        limits: e.rateLimits.map(l => ({ kind: l.kind, pct: l.percentUsed, resetsAt: l.resetsAt })),
      }))
    }
    return next(e)
  })

  // A main-loop request that got an answer restarts the cache TTL (subagents cache their own prefix).
  on('turn.step', async function* ($, e, next) {
    if (e.agentId || (await isOff($, MOD))) return yield* next(e)
    const sentAt = await $.clock.now()
    const result = yield* next(e)
    if (result.usage) await update($, lastHit, prev => Math.max(prev ?? 0, sentAt))
    return result
  })

  on('command.run', { command: 'gauge' }, async ($, e) => {
    const a = e.args.trim()
    if (a === '5m' || a === '1h') ttl = a
    const s = await read($, snap)
    const hit = await read($, lastHit)
    const left = hit == null ? null : TTL[ttl] - ((await $.clock.now()) - hit)
    return { text: plain(s.ctxPct, left, s.limits) + `  (cache TTL ${ttl})` }
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.props.hasSurvey || (await isOff($, MOD))) return next(e)
    const s = await read($, snap)
    const hit = await read($, lastHit)
    const left = hit == null ? null : TTL[ttl] - ((await $.clock.now()) - hit)
    if (s.ctxPct == null && !s.limits.length && left == null) return next(e)
    const { Box, Text } = $.ui.resolve(e)
    const below = await next(e)
    return (
      <Box flexDirection="column">
        <Box flexDirection="row" flexWrap="wrap">
          <Text>ctx </Text>
          <Text color={s.ctxPct != null && s.ctxPct >= 80 ? 'red' : s.ctxPct != null && s.ctxPct >= 60 ? 'yellow' : 'green'}>
            {s.ctxPct == null ? '--' : `${bar(s.ctxPct, 6)} ${Math.round(s.ctxPct)}%`}
          </Text>
          <Text dimColor>  · cache </Text>
          {left == null ? <Text dimColor>--:--</Text> : <Text color={ttlColor(left, TTL[ttl])}>{clock(left)}</Text>}
          {s.limits.map(l => {
            const f = fuel(l)
            return (
              <Box key={l.kind} flexDirection="row">
                <Text dimColor>  · {f.name} E </Text>
                <Text color={fuelColor(f.left)}>{bar(f.left, 6)}</Text>
                <Text dimColor> F </Text>
                <Text color={fuelColor(f.left)}>{f.left}%</Text>
              </Box>
            )
          })}
        </Box>
        {below}
      </Box>
    )
  })
}
