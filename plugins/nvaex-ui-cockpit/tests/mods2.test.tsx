// Engine-level tests of the five added mods: commands run through the hooks, panes are mounted and pressed.
// Nothing sits beneath the plugin, so each `on` stands for the engine (fs, process, env, prompt, ui.open).
import { expect, test } from 'claude-code/testing'

const pane = (id: string, surface: 'terminal' | 'desktop' = 'terminal') => ({
  plugin: 'nvaex-ui-cockpit', component: 'Pane', requestId: id, surface,
  props: { title: id, isFocused: false, bodyColumns: 60, placement: 'dock', scroll: { offset: 0, bodyRows: 30 }, view: {} },
}) as const

function base(on: any, run: (argv: string[]) => { exitCode: number; stdout: string; stderr: string } = () => ({ exitCode: 1, stdout: '', stderr: '' })) {
  const opened: string[] = []
  on('command.register', () => ({ value: { command: 'x' } }))
  on('clock.now', () => ({ value: 1_000_000 }))
  on('ui.open', (_: any, e: any) => { opened.push(e.id); return { value: { isPlaced: true } } })
  on('session.start', (_: any, e: any) => ({ cwd: e.cwd }))
  on('session.root', () => ({ value: '/r' }))
  on('process.run', (_: any, e: any) => ({ value: run(e.command ?? e.argv ?? e) }))
  return opened
}

test('file tree: lists root, opens a folder on press, shows its files', async ($, on) => {
  const opened = base(on)
  on('fs.list', (_: any, e: any) => ({ value: e.path === '/r'
    ? [{ name: 'zeta.txt', kind: 'file', size: 1 }, { name: 'src', kind: 'dir', size: 0 }, { name: 'node_modules', kind: 'dir', size: 0 }]
    : [{ name: 'main.ts', kind: 'file', size: 9 }] }))
  await $.session.start({ cwd: '/r', surface: 'terminal', isInteractive: true })
  const r = await $.command.run({ command: 'files', args: '' })
  expect(JSON.stringify(r)).toMatch(/\/r: 3 entries/)
  expect(opened).toContain('nvaex-files')
  const ui = await $.ui.mount(pane('nvaex-files'))
  expect(await ui.find({ type: 'Text', text: /zeta\.txt/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /node_modules/ })).toBeUndefined()
  expect(await ui.find({ type: 'Text', text: /main\.ts/ })).toBeUndefined()
  await ui.press({ key: 'd:/r/src' })
  expect(await ui.find({ type: 'Text', text: /main\.ts/ })).toBeDefined()
  await ui.unmount()
})

test('agent configs: lists marketplaces, cycles, applies a profile by argv', async ($, on) => {
  const seen: string[][] = []
  base(on, argv => {
    seen.push(argv)
    if (argv.some(a => /agentconfigs\.py$/.test(a))) return { exitCode: 0, stderr: '', stdout: 'market\tm1\t3 plugins\towner/m1\nwf\tdocs\toff\tharness-scope profile\nwf\twriting\toff\tharness-scope profile\npkg\tnvaex-x@m\ton\tbuilder' }
    return { exitCode: /killswitch/.test(argv.join(' ')) ? 1 : 0, stdout: 'ok', stderr: '' }
  })
  await $.session.start({ cwd: '/r', surface: 'terminal', isInteractive: true })
  await $.command.run({ command: 'configs', args: '' })
  const ui = await $.ui.mount(pane('nvaex-configs'))
  expect(await ui.find({ type: 'Text', text: /m1 {2}3 plugins {2}owner\/m1/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /> workflow docs/ })).toBeDefined()
  await ui.press({ key: 'cfg-next' })
  expect(await ui.find({ type: 'Text', text: /> workflow writing/ })).toBeDefined()
  await ui.press({ key: 'cfg-next' })
  expect(await ui.find({ type: 'Text', text: /> package {1,2}nvaex-x@m/ })).toBeDefined()
  await ui.press({ key: 'cfg-apply' })
  expect(seen.some(a => a.join(' ') === 'claude plugin disable nvaex-x@m')).toBe(true)
  await ui.press({ key: 'cfg-next' }) // wraps to the first workflow
  await ui.press({ key: 'cfg-apply' })
  expect(seen.some(a => a[0] === 'python3' && a.includes('use') && a.includes('docs') && a.includes('--repo'))).toBe(true)
  await ui.unmount()
})

test('top button row: a press runs the mod command; an off mod has no button', async ($, on) => {
  const opened = base(on, argv => ({ exitCode: /killswitch/.test(argv.join(' ')) && /jev-panel/.test(argv.join(' ')) ? 0 : 1, stdout: '', stderr: '' }))
  on('fs.list', () => ({ value: [] }))
  on('ui.render', ($: any, e: any) => { const { Text } = $.ui.resolve(e); return <Text>engine</Text> })
  await $.session.start({ cwd: '/r', surface: 'terminal', isInteractive: true })
  const band = { plugin: 'nvaex-ui-cockpit', component: 'AbovePrompt', requestId: 'band', surface: 'terminal',
    props: { hasSurvey: false, isWorking: false, maxRows: 5, bodyColumns: 80, scroll: { offset: 0, bodyRows: 5 }, view: {} } } as const
  const ui = await $.ui.mount(band)
  expect(await ui.find({ key: 'btn-files' })).toBeDefined()
  expect(await ui.find({ key: 'btn-jev' })).toBeUndefined()
  expect(await ui.find({ type: 'Text', text: /engine/ })).toBeDefined()
  await ui.press({ key: 'btn-files' })
  expect(opened).toContain('nvaex-files')
  await ui.unmount()
})

test('browser cards: a browser tool result raises a card; option and typed reply go to the chat', async ($, on) => {
  base(on)
  const sent: string[] = []
  on('prompt.submit', (_: any, e: any) => { sent.push(e.text); return { text: e.text } })
  let out = 'CHOICE: Which login? | Work | Personal'
  on('tool.call', () => ({ result: {}, text: out }))
  await $.session.start({ cwd: '/r', surface: 'terminal', isInteractive: true })
  await $.tool.call({ tool: 'mcp__claw__browser', url: 'x' } as any)
  let ui = await $.ui.mount(pane('nvaex-cards'))
  expect(await ui.find({ type: 'Text', text: /Which login\?/ })).toBeDefined()
  const work = await ui.find({ type: 'Button', text: /Work/ })
  expect(work).toBeDefined()
  await ui.press({ key: (work as any).key })
  expect(sent).toEqual(['Browser choice "Which login?": Work'])
  await ui.unmount()
  // not a browser tool: no card
  out = 'CHOICE: Ignore me | a'
  await $.tool.call({ tool: 'Bash', command: 'echo' } as any)
  ui = await $.ui.mount(pane('nvaex-cards'))
  expect(await ui.find({ type: 'Text', text: /No browser choices pending/ })).toBeDefined()
  // typed reply through the drop-down prompt bar
  out = '{"choice":{"question":"Cookie banner?","options":["Accept","Reject"]}}'
  await $.tool.call({ tool: 'mcp__chrome__click', x: 1 } as any)
  await ui.unmount()
  ui = await $.ui.mount(pane('nvaex-cards'))
  const t = await ui.find({ type: 'Button', text: /Type a reply/ })
  await ui.press({ key: (t as any).key })
  const id = (t as any).key.replace('type:', '')
  await ui.input({ key: `in:${id}`, text: 'use the guest option' })
  expect(sent[1]).toBe('Browser choice "Cookie banner?": use the guest option')
  await ui.unmount()
})

test('jev panel: shows the route line and decisions; says plainly when files are absent', async ($, on) => {
  base(on)
  on('env.get', () => ({ value: '/h' }))
  let msgs: any[] = [{ role: 'user', content: [{ type: 'text', text: 'JEV route: L2 | groups code/ops | try a, b' }] }]
  on('session.messages', () => ({ value: msgs }))
  let files: Record<string, string> = { '/h/.nvaex/decisions.jsonl': '{"decision":"use sqlite","rejected":["postgres"]}\n{"decision":"old","status":"superseded"}\nnot json\n' }
  on('fs.read', (_: any, e: any) => (e.path in files ? { value: files[e.path] } : { deny: 'ENOENT' }))
  await $.session.start({ cwd: '/r', surface: 'terminal', isInteractive: true })
  await $.command.run({ command: 'jev', args: '' })
  let ui = await $.ui.mount(pane('nvaex-jev'))
  expect(await ui.find({ type: 'Text', text: /Routing tier: L2 \| groups code\/ops/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /use sqlite \(not postgres\)/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /Scorecard: file not found/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /old/ })).toBeUndefined()
  await ui.unmount()
  files = {}
  msgs = []
  await $.command.run({ command: 'jev', args: '' })
  ui = await $.ui.mount(pane('nvaex-jev'))
  expect(await ui.find({ type: 'Text', text: /Routing tier: not found/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /Decisions: file not found/ })).toBeDefined()
  await ui.unmount()
})
