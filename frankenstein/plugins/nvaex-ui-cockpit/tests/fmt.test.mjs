import assert from 'node:assert/strict'
import { bar, clock, fuel, ttlColor, plain } from '../hooks/lib/gauge-fmt.ts'
assert.equal(clock(300000), '5:00'); assert.equal(clock(0), '0:00'); assert.equal(clock(-5), '0:00'); assert.equal(clock(61000), '1:01')
assert.equal(bar(50, 8), '████░░░░'); assert.equal(bar(150, 4), '████'); assert.equal(bar(-1, 4), '░░░░')
assert.deepEqual(fuel({ kind: 'five_hour', pct: 29 }), { name: '5h', left: 71 })
assert.equal(ttlColor(30000, 300000), 'red')
assert.equal(plain(40, 252000, [{ kind: 'seven_day', pct: 10 }]), 'ctx ██░░░░ 40% · cache 4:12 · 7d 90% left')
console.log('fmt ok')
