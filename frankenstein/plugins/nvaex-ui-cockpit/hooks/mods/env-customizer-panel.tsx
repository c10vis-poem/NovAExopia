// Mod 2. Profile switcher over harness-scope profiles: global / marketplaces / repo overview, pick a
// profile for this repo. Writes only <repo>/.claude/harness-scope.json (a one-line selector), never settings.
// Off alone: touch ~/.claude/state/off/nvaex-ui-cockpit.env-customizer-panel
import type { EngineInterface, Register } from 'claude-code'
import { isOff, py } from '../lib/gate'

const MOD = 'env-customizer-panel'
const PANE = 'nvaex-env'

let scopes = ''
let names: string[] = []
let current = ''
let note = ''

async function refresh($: EngineInterface) {
  const repo = await $.session.root()
  scopes = await py($, 'profiles.py', ['scopes', '--repo', repo])
  const rows = (await py($, 'profiles.py', ['list', '--repo', repo])).split('\n').filter(Boolean)
  names = rows.map(r => r.slice(2).trim())
  current = rows.find(r => r.startsWith('*'))?.slice(2).trim() ?? ''
  $.ui.invalidate('ui.render')
}

async function use($: EngineInterface, name: string) {
  const repo = await $.session.root()
  note = await py($, 'profiles.py', name === '(none)' ? ['clear', '--repo', repo] : ['use', name, '--repo', repo])
  await refresh($)
}

export async function init($: EngineInterface) {
  await $.command.register({ name: 'env', description: 'Environment profiles: /env, /env use NAME, /env clear' })
}

export const mount = (on: Parameters<Register>[0]) => {
  on('command.run', { command: 'env' }, async ($, e) => {
    if (await isOff($, MOD)) return { text: 'env-customizer-panel is switched off (kill switch).' }
    const [verb, name] = e.args.trim().split(/\s+/)
    if (verb === 'use' && name) await use($, name)
    else if (verb === 'clear') await use($, '(none)')
    else {
      await refresh($)
      await $.ui.open({ id: PANE, title: 'Environment' })
    }
    return { text: note || scopes }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text, Select } = $.ui.resolve(e)
    return (
      <Box flexDirection="column">
        {scopes.split('\n').map(l => (
          <Text>{l}</Text>
        ))}
        <Select
          key="env-profile"
          label="Profile for this repo: "
          value={current || '(none)'}
          options={['(none)', ...names].map(value => ({ value }))}
          onSelect={v => void use($, v)}
        />
        {note ? <Text dimColor>{note}</Text> : null}
      </Box>
    )
  })
}
