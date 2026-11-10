// Mod 7. Button row across the top of the prompt area. The API has no screen-top slot, only the band above the
// prompt (AbovePrompt), so the row lives there. A button opens another mod's pane by calling that mod's open()
// directly (a plugin's own `$.command.run` skips its own hooks, so it cannot go through the slash command).
// An off mod's button disappears. Off alone: touch ~/.claude/state/off/nvaex-ui-cockpit.top-button-row
import type { EngineInterface, Register } from 'claude-code'
import { isOff } from '../lib/gate'
import { BUTTONS, keyOf } from '../lib/buttons'
import { open as openPlugins } from './plugins-panel'
import { open as openFiles } from './file-tree-panel'
import { open as openConfigs } from './agent-configs-panel'
import { open as openEnv } from './env-customizer-panel'
import { open as openTree } from './obsidian-config-tree'
import { open as openCtx } from './context-window'
import { open as openJev } from './jev-panel'
import { open as openCards } from './browser-cards'

const MOD = 'top-button-row'

async function run($: EngineInterface, command: string) {
  try {
    if (command === 'plugins-panel') await openPlugins($)
    else if (command === 'files') await openFiles($)
    else if (command === 'configs') await openConfigs($)
    else if (command === 'env') await openEnv($)
    else if (command === 'config-tree') await openTree($)
    else if (command === 'context-window') await openCtx($)
    else if (command === 'jev') await openJev($)
    else if (command === 'cards') await openCards($)
  } catch (err) {
    $.ui.toast(`${command} failed: ${String(err)}`)
  }
}

export async function init(_$: EngineInterface) {}

export const mount = (on: Parameters<Register>[0]) => {
  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.props.hasSurvey || (await isOff($, MOD))) return next(e)
    const shown = []
    for (const b of BUTTONS) if (!(await isOff($, b.mod))) shown.push(b)
    if (!shown.length) return next(e)
    const { Box, Text, Button } = $.ui.resolve(e)
    const below = await next(e)
    return (
      <Box flexDirection="column">
        <Box>
          {shown.map(b => (
            <Button key={keyOf(b)} onPress={() => void run($, b.command)}>{b.label}</Button>
          ))}
        </Box>
        {below}
      </Box>
    )
  })
}
