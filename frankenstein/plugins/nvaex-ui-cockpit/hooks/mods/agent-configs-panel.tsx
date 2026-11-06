// Mod 6. Agent-configs side panel: marketplaces, agent packages (toggle), workflows (harness-scope profiles),
// and Prev/Next/Apply to cycle between them. Writes only via `claude plugin enable|disable` and profiles.py (selector file).
// Off alone: touch ~/.claude/state/off/nvaex-ui-cockpit.agent-configs-panel
import type { EngineInterface, Register } from 'claude-code'
import { isOff, py } from '../lib/gate'
import { type Item, applyArgv, key, parse, ring, step } from '../lib/agentconfigs'

const MOD = 'agent-configs-panel'
const PANE = 'nvaex-configs'
let items: Item[] = []
let sel = ''
let note = ''

async function refresh($: EngineInterface) {
  const repo = await $.session.root()
  items = parse(await py($, 'agentconfigs.py', ['items', '--repo', repo]))
  if (!ring(items).some(i => key(i) === sel)) sel = ring(items)[0] ? key(ring(items)[0]) : ''
  $.ui.invalidate('ui.render')
}

async function apply($: EngineInterface) {
  const it = ring(items).find(i => key(i) === sel)
  const argv = it && applyArgv(it, await $.session.root(), `${$.plugin.root}/scripts`)
  if (!argv) { note = 'nothing to apply'; return }
  const r = await $.process.run(argv, { timeoutMs: 30000 })
  note = ((r.exitCode === 0 ? r.stdout : r.stderr || r.stdout) || `${it.name} done`).trim().split('\n')[0]
  await refresh($)
}

function go($: EngineInterface, dir: 1 | -1) {
  sel = step(ring(items), sel, dir)
  $.ui.invalidate('ui.render')
}

export async function init($: EngineInterface) {
  await $.command.register({ name: 'configs', description: 'Agent configs pane: marketplaces, agent packages, workflows. `/configs next|prev|apply` cycles' })
}

export async function open($: EngineInterface) {
  await refresh($)
  await $.ui.open({ id: PANE, title: 'Agent configs' })
}

export const mount = (on: Parameters<Register>[0]) => {
  on('command.run', { command: 'configs' }, async ($, e) => {
    if (await isOff($, MOD)) return { text: 'agent-configs-panel is switched off (kill switch).' }
    const verb = e.args.trim()
    if (!items.length || verb === '') await refresh($)
    if (verb === 'next') go($, 1)
    else if (verb === 'prev') go($, -1)
    else if (verb === 'apply') await apply($)
    else await $.ui.open({ id: PANE, title: 'Agent configs' })
    return { text: note || `${items.filter(i => i.kind === 'market').length} marketplaces, ${ring(items).length} workflows/packages; selected ${sel || 'none'}` }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text, Button } = $.ui.resolve(e)
    const r = ring(items)
    return (
      <Box flexDirection="column">
        <Text bold>Marketplaces</Text>
        {items.filter(i => i.kind === 'market').map(i => <Text>{`  ${i.name}  ${i.state}  ${i.detail}`}</Text>)}
        <Text bold>Workflows and agent packages</Text>
        {r.map(i => <Text dimColor={key(i) !== sel}>{`${key(i) === sel ? '>' : ' '} ${i.kind === 'wf' ? 'workflow' : 'package '} ${i.name} [${i.state}]  ${i.detail}`}</Text>)}
        <Box>
          <Button key="cfg-prev" onPress={() => go($, -1)}>Prev</Button>
          <Text> </Text>
          <Button key="cfg-next" onPress={() => go($, 1)}>Next</Button>
          <Text> </Text>
          <Button key="cfg-apply" variant="primary" onPress={() => void apply($)}>Apply</Button>
        </Box>
        {note ? <Text dimColor>{note}</Text> : null}
      </Box>
    )
  })
}
