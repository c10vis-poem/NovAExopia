import assert from 'node:assert/strict'
import { rows, lines } from '../hooks/lib/ctx-rows.ts'
const r = rows([
  { role: 'user', content: 'x'.repeat(40) },
  { role: 'assistant', content: [{ type: 'tool_use', id: 'a', name: 'Bash', input: { cmd: 'ls' } }] },
  { role: 'user', content: [{ type: 'tool_result', tool_use_id: 'a', content: 'y'.repeat(4000) }] },
])
assert.deepEqual(r.map(x => x.kind + ':' + x.name), ['user:user', 'tool_use:Bash', 'tool_result:Bash'])
assert.equal(r[2].tokens, 1000)
assert.match(lines(r)[0], /^tool_result:Bash  x1  ~1000 tok$/)
assert.deepEqual(rows([]), [])
console.log('ctx ok')
