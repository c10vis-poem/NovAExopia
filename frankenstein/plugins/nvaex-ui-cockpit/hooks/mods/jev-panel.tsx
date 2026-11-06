// Mod 9. Jev side panel: routing tier and recent decisions. Hot-swap: no dependency on nvaex-jev-core. It reads
// the router's "JEV route:" line from the conversation and the ledger files jev-core reads/writes, and says plainly
// when any is absent. Off alone: touch ~/.claude/state/off/nvaex-ui-cockpit.jev-panel
import type { EngineInterface, Register } from 'claude-code'
import { isOff } from '../lib/gate'
import { latestRoute, textsOf, view } from '../lib/jev'

const MOD = 'jev-panel'
const PANE = 'nvaex-jev'
let shown: string[] = ['(not loaded)']

async function read($: EngineInterface, p: string) {
  try { return await $.fs.read(p) } catch { return null }
}

async function refresh($: EngineInterface) {
  const home = (await $.env.get('HOME')) ?? ''
  const proj = await $.session.root()
  let msgs: any[] = []
  try { msgs = (await $.session.messages({ as: 'api' })) as any[] } catch {}
  const g = await read($, `${home}/.nvaex/decisions.jsonl`)
  const p = await read($, `${proj}/.nvaex/decisions.jsonl`)
  shown = view({
    route: latestRoute(textsOf(msgs)),
    decisions: g === null && p === null ? null : `${p ?? ''}\n${g ?? ''}`,
    scorecard: await read($, `${home}/.claude/state/nvaex-jev-core/scorecard.jsonl`),
  })
  $.ui.invalidate('ui.render')
}

export async function init($: EngineInterface) {
  await $.command.register({ name: 'jev', description: 'Jev pane: routing tier, recent decisions, last scorecard (reads nvaex-jev-core files if present)' })
}

export async function open($: EngineInterface) {
  try { await refresh($) } catch (err) { shown = [`jev-panel failed: ${String(err)}`] }
  await $.ui.open({ id: PANE, title: 'Jev' })
}

export const mount = (on: Parameters<Register>[0]) => {
  on('command.run', { command: 'jev' }, async ($, e) => {
    if (await isOff($, MOD)) return { text: 'jev-panel is switched off (kill switch).' }
    await open($)
    return { text: shown[0] }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    return <Box flexDirection="column">{shown.map(l => <Text>{l}</Text>)}</Box>
  })
}
