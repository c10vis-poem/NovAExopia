// nvaex-ui-cockpit: one hooks module composing independent mods. Each mod checks its own kill
// switch (~/.claude/state/off/nvaex-ui-cockpit.<mod>), so any one can be swapped out alone.
// One hook per lifecycle event per package (CONTRACT rule 4): session.start lives here and calls each init.
import type { Register } from 'claude-code'
import { init as i1, mount as plugins } from './mods/plugins-panel'
import { init as i2, mount as env } from './mods/env-customizer-panel'
import { init as i3, mount as tree } from './mods/obsidian-config-tree'
import { init as i4, mount as ctx } from './mods/context-window'
import { init as i5, mount as files } from './mods/file-tree-panel'
import { init as i6, mount as configs } from './mods/agent-configs-panel'
import { init as i7, mount as row } from './mods/top-button-row'
import { init as i8, mount as cards } from './mods/browser-cards'
import { init as i9, mount as jev } from './mods/jev-panel'

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    // fail open: one mod's init error must not stop the others
    try { await i1($) } catch {}
    try { await i2($) } catch {}
    try { await i3($) } catch {}
    try { await i4($) } catch {}
    try { await i5($) } catch {}
    try { await i6($) } catch {}
    try { await i7($) } catch {}
    try { await i8($) } catch {}
    try { await i9($) } catch {}
    return next(e)
  })
  plugins(on)
  env(on)
  tree(on)
  ctx(on)
  files(on)
  configs(on)
  row(on)
  cards(on)
  jev(on)
}
