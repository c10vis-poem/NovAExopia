// Mod 4. Pane listing what entered context (messages, tool calls, results) with chars/4 estimates. No token limits or rate data.
// Idea from context-window (MIT). Off alone: touch ~/.claude/state/off/nvaex-ui-cockpit.context-window
import type { EngineInterface, Register } from 'claude-code'
import { isOff } from '../lib/gate'
import { lines, rows } from '../lib/ctx-rows'

const MOD = 'context-window'
const PANE = 'nvaex-context'
let shown: string[] = []

async function refresh($: EngineInterface) {
  const msgs = (await $.session.messages({ as: 'api' })) as any[]
  shown = Array.isArray(msgs) && msgs.length ? lines(rows(msgs)) : ['(no messages yet)']
  $.ui.invalidate('ui.render')
}

export async function init($: EngineInterface) {
  await $.command.register({ name: 'context-window', description: 'Open the context pane: what entered the conversation, by kind and tool' })
}

export async function open($: EngineInterface) {
  try { await refresh($) } catch (err) { shown = [`context-window failed: ${String(err)}`] }
  await $.ui.open({ id: PANE, title: 'Context' })
}

export const mount = (on: Parameters<Register>[0]) => {
  on('command.run', { command: 'context-window' }, async $ => {
    if (await isOff($, MOD)) return { text: 'context-window is switched off (kill switch).' }
    await open($)
    return { text: shown.slice(0, 8).join('\n') }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    const room = Math.max(1, (e.viewport?.rows ?? 24) - 3)
    return (
      <Box flexDirection="column">
        {shown.slice(0, room).map(l => <Text>{l}</Text>)}
      </Box>
    )
  })
}
