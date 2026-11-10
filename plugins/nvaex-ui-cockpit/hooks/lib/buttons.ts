// Pure: the top button row. Each entry runs a slash command of another mod; a mod that is off drops its button.
export type Btn = { mod: string; label: string; command: string }
export const BUTTONS: Btn[] = [
  { mod: 'plugins-panel', label: 'Plugins', command: 'plugins-panel' },
  { mod: 'file-tree-panel', label: 'Files', command: 'files' },
  { mod: 'agent-configs-panel', label: 'Configs', command: 'configs' },
  { mod: 'env-customizer-panel', label: 'Env', command: 'env' },
  { mod: 'obsidian-config-tree', label: 'Tree', command: 'config-tree' },
  { mod: 'context-window', label: 'Context', command: 'context-window' },
  { mod: 'jev-panel', label: 'Jev', command: 'jev' },
  { mod: 'browser-cards', label: 'Cards', command: 'cards' },
]
export const visible = (off: (mod: string) => boolean) => BUTTONS.filter(b => !off(b.mod))
export const keyOf = (b: Btn) => `btn-${b.command}`
export const byKey = (k: string) => BUTTONS.find(b => keyOf(b) === k)
