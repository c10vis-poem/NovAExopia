// Mod 1. Above-prompt "Plugins: A/N active" that expands into a pane (agents, skills, hooks, token footprint).
// Data: scripts/inventory.py (read-only). Off alone: touch ~/.claude/state/off/nvaex-ui-cockpit.plugins-panel
import type { EngineInterface, Register } from 'claude-code'
import { isOff, py } from '../lib/gate'

const MOD = 'plugins-panel'
const PANE = 'nvaex-plugins'

let summary = ''
let list = ''

async function refresh($: EngineInterface) {
  summary = await py($, 'inventory.py', ['summary'])
  list = await py($, 'inventory.py', ['list'])
  $.ui.invalidate('ui.render')
}

export async function init($: EngineInterface) {
  await $.command.register({ name: 'plugins-panel', description: 'Open the plugins pane: what each active plugin adds and costs' })
  if (!(await isOff($, MOD))) await refresh($)
}

export const mount = (on: Parameters<Register>[0]) => {

  on('command.run', { command: 'plugins-panel' }, async $ => {
    if (await isOff($, MOD)) return { text: 'plugins-panel is switched off (kill switch).' }
    await refresh($)
    await $.ui.open({ id: PANE, title: 'Plugins' })
    return { text: summary }
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.props.hasSurvey || !summary || (await isOff($, MOD))) return next(e)
    const { Box, Text } = $.ui.resolve(e)
    const below = await next(e)
    return (
      <Box flexDirection="column">
        <Text dimColor>{summary}  (/plugins-panel)</Text>
        {below}
      </Box>
    )
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    const room = Math.max(1, (e.viewport?.rows ?? 24) - 3)
    return (
      <Box flexDirection="column">
        {list.split('\n').slice(0, room).map(l => (
          <Text dimColor={l.startsWith('off')}>{l}</Text>
        ))}
      </Box>
    )
  })
}
