import assert from 'node:assert/strict'
import { rowsOf, label } from '../hooks/lib/filetree.ts'
import { parse, ring, step, key, applyArgv } from '../hooks/lib/agentconfigs.ts'
import { parseChoice, isBrowserTool, push, drop, reply } from '../hooks/lib/cards.ts'
import { view, latestRoute, jsonl, textsOf } from '../hooks/lib/jev.ts'
import { visible, BUTTONS } from '../hooks/lib/buttons.ts'

// file tree: dirs first, noise skipped, only open dirs expanded, cap honoured
const cache = new Map([
  ['/r', [{ name: 'b.txt', kind: 'file' }, { name: 'src', kind: 'dir' }, { name: '.git', kind: 'dir' }, { name: 'a', kind: 'dir' }]],
  ['/r/src', [{ name: 'x.ts', kind: 'file' }]],
])
assert.deepEqual(rowsOf('/r', cache, new Set()).map(r => r.name), ['a', 'src', 'b.txt'])
const o = rowsOf('/r', cache, new Set(['/r/src']))
assert.deepEqual(o.map(r => r.name), ['a', 'src', 'x.ts', 'b.txt'])
assert.equal(o[2].depth, 1)
assert.equal(label(o[1]), 'v src/')
assert.equal(rowsOf('/r', cache, new Set(['/r/src']), 2).length, 2)

// agent configs
const items = parse('market\tm\t3 plugins\to/m\nwf\tdocs\toff\tp\nwf\twriting\ton\tp\npkg\tnvaex-x@m\ton\tbuilder\ngarbage\nwf\t\t\t')
assert.equal(items.length, 4)
const r = ring(items)
assert.deepEqual(r.map(key), ['wf:docs', 'wf:writing', 'pkg:nvaex-x@m'])
assert.equal(step(r, 'wf:docs', 1), 'wf:writing')
assert.equal(step(r, 'pkg:nvaex-x@m', 1), 'wf:docs')
assert.equal(step(r, 'wf:docs', -1), 'pkg:nvaex-x@m')
assert.equal(step(r, '', 1), 'wf:docs')
assert.equal(step(r, '', -1), 'pkg:nvaex-x@m')
assert.equal(step([], 'x', 1), '')
assert.deepEqual(applyArgv(r[2], '/repo', '/s'), ['claude', 'plugin', 'disable', 'nvaex-x@m'])
assert.deepEqual(applyArgv({ kind: 'pkg', name: 'p', state: 'off', detail: '' }, '/repo', '/s'), ['claude', 'plugin', 'enable', 'p'])
assert.deepEqual(applyArgv(r[0], '/repo', '/s'), ['python3', '/s/profiles.py', 'use', 'docs', '--repo', '/repo'])
assert.equal(applyArgv({ kind: 'pkg', name: 'x;rm -rf ~', state: 'on', detail: '' }, '/r', '/s'), null)
assert.equal(applyArgv({ kind: 'wf', name: '../evil', state: 'off', detail: '' }, '/r', '/s'), null)
assert.equal(applyArgv(items[0], '/r', '/s'), null)

// browser cards
assert.ok(isBrowserTool('mcp__claw__browser') && isBrowserTool('mcp__plugin_tinyfish_tinyfish__x') && !isBrowserTool('Bash'))
const c1 = parseChoice('noise\nCHOICE: Which login? | Work | Personal\nmore', 't')
assert.deepEqual([c1.question, c1.options], ['Which login?', ['Work', 'Personal']])
const c2 = parseChoice('result {"choice":{"question":"Banner?","options":["Accept","Reject"]}} end', 't')
assert.deepEqual([c2.question, c2.options], ['Banner?', ['Accept', 'Reject']])
assert.equal(parseChoice('CHOICE: only a question', 't'), null)
assert.equal(parseChoice('{"choice":{"question":"q","options":[]}}', 't'), null)
assert.equal(parseChoice('{"choice":{"question":"q","options":[}}', 't'), null)
assert.equal(parseChoice('plain page text', 't'), null)
let cs = push([], c1); cs = push(cs, c1); assert.equal(cs.length, 1)
for (let i = 0; i < 9; i++) cs = push(cs, { ...c2, id: 'i' + i })
assert.equal(cs.length, 5)
assert.equal(drop(cs, 'i8').length, 4)
assert.equal(reply(c1, 'Work'), 'Browser choice "Which login?": Work')

// jev
assert.equal(latestRoute(['x', 'JEV route: L1 | groups a', 'y', 'JEV route: L3 | groups b/c | try z']), 'L3 | groups b/c | try z')
assert.equal(latestRoute(['none']), null)
assert.deepEqual(jsonl('{"a":1}\nbad\n\n{"b":2}'), [{ a: 1 }, { b: 2 }])
assert.deepEqual(textsOf([{ content: 'a' }, { content: [{ text: 'b' }, { type: 'tool_use' }] }]), ['a', 'b'])
const absent = view({ route: null, decisions: null, scorecard: null }).join('\n')
assert.match(absent, /Routing tier: not found/); assert.match(absent, /Decisions: file not found/); assert.match(absent, /Scorecard: file not found/)
const present = view({ route: 'L2 | groups a', decisions: '{"decision":"use sqlite","rejected":["pg"]}\n{"decision":"gone","status":"superseded"}', scorecard: '{"pass":25}' }).join('\n')
assert.match(present, /Routing tier: L2/); assert.match(present, /use sqlite \(not pg\)/); assert.doesNotMatch(present, /gone/); assert.match(present, /Last scorecard: \{"pass":25\}/)
assert.match(view({ route: null, decisions: '', scorecard: '' }).join('\n'), /none active/)

// button row
assert.equal(visible(() => false).length, BUTTONS.length)
assert.ok(!visible(m => m === 'jev-panel').some(b => b.command === 'jev'))
console.log('libs ok')
