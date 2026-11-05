// Mod 3. Searchable tree of every enabled skill, agent, command, hook and script with a one-line
// plain-English explanation. /config-tree [query] opens it; the search box filters live.
// Off alone: touch ~/.claude/state/off/nvaex-ui-cockpit.obsidian-config-tree
import type { EngineInterface, Register } from 'claude-code'
import { isOff, py } from '../lib/gate'

const MOD = 'obsidian-config-tree'
const PANE = 'nvaex-config-tree'

let query = ''
let lines: string[] = []

async function load($: EngineInterface, q: string) {
  query = q
  lines = (await py($, 'configtree.py', q ? [q] : [])).split('\n')
  $.ui.invalidate('ui.render')
}

export async function init($: EngineInterface) {
  await $.command.register({ name: 'config-tree', description: 'Searchable tree of skills, agents, commands, hooks and scripts, each explained in one line' })
}

export const mount = (on: Parameters<Register>[0]) => {
  on('command.run', { command: 'config-tree' }, async ($, e) => {
    if (await isOff($, MOD)) return { text: 'obsidian-config-tree is switched off (kill switch).' }
    await load($, e.args.trim())
    await $.ui.open({ id: PANE, title: 'Config tree' })
    return { text: `${lines.length} lines` + (query ? ` matching "${query}"` : '') }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text, Input } = $.ui.resolve(e)
    const room = Math.max(1, (e.viewport?.rows ?? 24) - 5)
    return (
      <Box flexDirection="column">
        <Input key="tree-q" label="Search: " placeholder="skill, hook, word..." value={query} onSubmit={v => void load($, v)} />
        {lines.slice(0, room).map(l => (
          <Text dimColor={l.startsWith('  ')}>{l}</Text>
        ))}
        {lines.length > room ? <Text dimColor>... {lines.length - room} more, narrow the search</Text> : null}
      </Box>
    )
  })
}
