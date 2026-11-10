import { expect, test } from 'claude-code/testing'

function engine(on: any, killExit: number, run: (cmd: string[]) => any = () => ({ exitCode: 0, stdout: '', stderr: '' })) {
  on('command.register', () => ({ value: { command: 'x' } }))
  on('process.run', (_: any, e: any) => ({ value: run(e.command ?? e.argv ?? e) }))
  on('clock.now', () => ({ value: 1_000_000 }))
  on('ui.open', () => ({ value: {} }))
  on('ui.invalidate', () => ({ value: {} }))
  on('session.start', (_: any, e: any) => ({ cwd: e.cwd }))
  void killExit
}

test('plugins-panel on NAME runs claude plugin enable', async ($, on) => {
  const seen: string[] = []
  engine(on, 1, c => { seen.push(JSON.stringify(c)); return { exitCode: /killswitch/.test(JSON.stringify(c)) ? 1 : 0, stdout: 'ok enabled', stderr: '' } })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  const r = await $.command.run({ command: 'plugins-panel', args: 'on demo@m' })
  expect(JSON.stringify(r)).toMatch(/ok enabled/)
  expect(seen.some(s => /"enable"/.test(s) && /demo@m/.test(s))).toBe(true)
})

test('plugins-panel rejects a shell-looking name', async ($, on) => {
  const seen: string[] = []
  engine(on, 1, c => { seen.push(JSON.stringify(c)); return { exitCode: 1, stdout: '', stderr: '' } })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.command.run({ command: 'plugins-panel', args: 'on x;rm -rf ~' })
  expect(seen.some(s => /"enable"/.test(s))).toBe(false)
})

test('context-window lists tool results', async ($, on) => {
  engine(on, 1, () => ({ exitCode: 1, stdout: '', stderr: '' }))
  on('session.messages', () => ({ value: [
    { role: 'assistant', content: [{ type: 'tool_use', id: 'a', name: 'Bash', input: {} }] },
    { role: 'user', content: [{ type: 'tool_result', tool_use_id: 'a', content: 'z'.repeat(400) }] },
  ] }))
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  const r = await $.command.run({ command: 'context-window', args: '' })
  expect(JSON.stringify(r)).toMatch(/tool_result:Bash/)
})
