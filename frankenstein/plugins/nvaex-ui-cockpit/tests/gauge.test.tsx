import { expect, test } from 'claude-code/testing'

const usage = {
  context: { window: 200000, tokens: 80000, percent: 40 },
  rateLimits: [
    { kind: 'five_hour', percentUsed: 29 },
    { kind: 'seven_day', percentUsed: 10 },
  ],
}

function engine(on: any, killExit: number) {
  on('command.register', () => ({ value: { command: 'x' } }))
  on('process.run', () => ({ value: { exitCode: killExit, stdout: '', stderr: '' } }))
  on('session.usage', () => ({ value: usage }))
  on('clock.now', () => ({ value: 1_000_000 }))
  on('session.start', (_: any, e: any) => ({ cwd: e.cwd }))
}

test('/gauge prints ctx, cache and fuel', async ($, on) => {
  engine(on, 1)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  const r = await $.command.run({ command: 'gauge', args: '' })
  expect(JSON.stringify(r)).toMatch(/ctx .*40%/)
  expect(JSON.stringify(r)).toMatch(/5h 71% left/)
  expect(JSON.stringify(r)).toMatch(/7d 90% left/)
})

test('band draws the gauge', async ($, on) => {
  engine(on, 1)
  on('ui.render', ($: any, e: any) => $.ui.resolve(e).Text({ children: ['engine'] }))
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  const props = { hasSurvey: false, bodyColumns: 80 }
  const base = { plugin: 'nvaex-ui-cockpit', component: 'AbovePrompt', requestId: 'band', props, surface: 'terminal' } as const
  const ui = await $.ui.mount(base)
  expect((await ui.find({ type: 'Text', text: /ctx/ }))?.text).toBeTruthy()
  await ui.unmount()
})

test('kill switch on: the band is the engine\'s alone', async ($, on) => {
  engine(on, 0)
  on('ui.render', ($: any, e: any) => $.ui.resolve(e).Text({ children: ['engine'] }))
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  const props = { hasSurvey: false, bodyColumns: 80 }
  const ui = await $.ui.mount({ plugin: 'nvaex-ui-cockpit', component: 'AbovePrompt', requestId: 'band', props, surface: 'terminal' } as const)
  expect(await ui.find({ type: 'Text', text: /ctx/ })).toBeFalsy()
  expect((await ui.find({ type: 'Text', text: /engine/ }))?.text).toBe('engine')
  await ui.unmount()
})
