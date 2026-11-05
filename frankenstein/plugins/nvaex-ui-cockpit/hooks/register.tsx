// nvaex-ui-cockpit: one hooks module composing four independent mods. Each mod checks its own kill
// switch (~/.claude/state/off/nvaex-ui-cockpit.<mod>), so any one can be swapped out alone.
// One hook per lifecycle event per package (CONTRACT rule 4): session.start lives here and calls each init.
import type { Register } from 'claude-code'
import { init as i1, mount as plugins } from './mods/plugins-panel'
import { init as i2, mount as env } from './mods/env-customizer-panel'
import { init as i3, mount as tree } from './mods/obsidian-config-tree'
import { init as i4, mount as gauge } from './mods/token-cache-gauge'

export const register: Register = (on, options) => {
  on('session.start', async ($, e, next) => {
    // fail open: one mod's init error must not stop the others
    try { await i1($) } catch {}
    try { await i2($) } catch {}
    try { await i3($) } catch {}
    try { await i4($) } catch {}
    return next(e)
  })
  plugins(on)
  env(on)
  tree(on)
  gauge(on, options)
}
