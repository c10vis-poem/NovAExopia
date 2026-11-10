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
  await $.command.register({ name: 'plugins-panel', description: 'Open the plugins pane: what each active plugin adds and costs. `on|off NAME` enables or disables one' })
  if (!(await isOff($, MOD))) await refresh($)
}

export async function open($: EngineInterface) {
  await refresh($)
  await $.ui.open({ id: PANE, title: 'Plugins' })
}

export const mount = (on: Parameters<Register>[0]) => {

  on('command.run', { command: 'plugins-panel' }, async ($, e) => {
    if (await isOff($, MOD)) return { text: 'plugins-panel is switched off (kill switch).' }
    // toggle idea from plugin-manager (MIT): `/plugins-panel on|off NAME[@MARKET]`, done by the claude CLI, never by editing settings
    const m = /^(on|off)\s+([\w.-]+(?:@[\w.-]+)?)\s*$/.exec(e.args.trim())
    if (m) {
      const r = await $.process.run(['claude', 'plugin', m[1] === 'on' ? 'enable' : 'disable', m[2]], { timeoutMs: 30000 })
      await refresh($)
      return { text: (r.exitCode === 0 ? r.stdout : r.stderr || r.stdout).trim() || `${m[2]} ${m[1]}` }
    }
    await open($)
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
