// Mod 5. File tree side panel: lazily listed, click a folder to open/close. Read-only ($.fs.list only).
// Off alone: touch ~/.claude/state/off/nvaex-ui-cockpit.file-tree-panel
import type { EngineInterface, Register } from 'claude-code'
import { isOff } from '../lib/gate'
import { type Ent, label, rowsOf } from '../lib/filetree'

const MOD = 'file-tree-panel'
const PANE = 'nvaex-files'
const cache = new Map<string, Ent[]>()
const opened = new Set<string>()
let root = ''
let note = ''

async function load($: EngineInterface, dir: string) {
  try {
    cache.set(dir, (await $.fs.list(dir)).map(x => ({ name: x.name, kind: x.kind, size: x.size })))
  } catch (err) {
    cache.set(dir, [])
    note = `cannot list ${dir}: ${String(err)}`
  }
}

async function toggle($: EngineInterface, path: string) {
  if (opened.has(path)) opened.delete(path)
  else { opened.add(path); if (!cache.has(path)) await load($, path) }
  $.ui.invalidate('ui.render')
}

export async function init($: EngineInterface) {
  await $.command.register({ name: 'files', description: 'Open the file tree pane for this workspace (or `/files /some/dir`)' })
}

export async function open($: EngineInterface, arg = '') {
  const next = arg.startsWith('/') ? arg : await $.session.root()
  if (next !== root) { root = next; cache.clear(); opened.clear(); note = '' }
  await load($, root)
  await $.ui.open({ id: PANE, title: 'Files' })
}

export const mount = (on: Parameters<Register>[0]) => {
  on('command.run', { command: 'files' }, async ($, e) => {
    if (await isOff($, MOD)) return { text: 'file-tree-panel is switched off (kill switch).' }
    await open($, e.args.trim())
    return { text: `${root}: ${cache.get(root)?.length ?? 0} entries` }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text, Button } = $.ui.resolve(e)
    const rows = rowsOf(root, cache, opened)
    return (
      <Box flexDirection="column">
        <Text dimColor>{root}</Text>
        {rows.map(r =>
          r.kind === 'dir' ? (
            <Button key={`d:${r.path}`} plain onPress={() => void toggle($, r.path)}>{label(r)}</Button>
          ) : (
            <Text dimColor={r.kind === 'other'}>{label(r)}</Text>
          ),
        )}
        {note ? <Text dimColor>{note}</Text> : null}
      </Box>
    )
  })
}
