// Mod 8. Browser choice cards. When a browser-driving tool's result carries a choice
// (`CHOICE: question | a | b` or {"choice":{"question":..,"options":[..]}}), a card pops up in a pane. An option button
// answers into the chat; "Type a reply" drops down a prompt bar on the card whose text goes into the chat.
// Off alone: touch ~/.claude/state/off/nvaex-ui-cockpit.browser-cards
import type { EngineInterface, Register } from 'claude-code'
import { isOff } from '../lib/gate'
import { type Card, drop, isBrowserTool, parseChoice, push, reply, textOf } from '../lib/cards'

const MOD = 'browser-cards'
const PANE = 'nvaex-cards'
let cards: Card[] = []
let typing = ''

async function answer($: EngineInterface, c: Card, text: string) {
  cards = drop(cards, c.id)
  if (typing === c.id) typing = ''
  $.ui.invalidate('ui.render')
  await $.prompt.submit({ text: reply(c, text) })
}

export async function init($: EngineInterface) {
  await $.command.register({ name: 'cards', description: 'Browser choice cards pending an answer. `/cards clear` drops them' })
}

export async function open($: EngineInterface) {
  await $.ui.open({ id: PANE, title: 'Choices' })
}

export const mount = (on: Parameters<Register>[0]) => {
  on('tool.call', async ($, e, next) => {
    const ran = await next(e)
    if (!isBrowserTool(String(e.tool)) || ran.deny !== undefined || (await isOff($, MOD))) return ran
    const c = parseChoice(textOf((ran as any).text ?? (ran as any).result), String(e.tool))
    if (c) {
      cards = push(cards, c)
      await $.ui.open({ id: PANE, title: 'Choices' })
      $.ui.invalidate('ui.render')
    }
    return ran
  })

  on('command.run', { command: 'cards' }, async ($, e) => {
    if (await isOff($, MOD)) return { text: 'browser-cards is switched off (kill switch).' }
    if (e.args.trim() === 'clear') { cards = []; typing = ''; $.ui.invalidate('ui.render'); return { text: 'cleared' } }
    await open($)
    return { text: cards.length ? cards.map(c => `${c.question} [${c.options.join(' | ')}]`).join('\n') : 'no browser choices pending' }
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.props.hasSurvey || !cards.length || (await isOff($, MOD))) return next(e)
    const { Box, Text } = $.ui.resolve(e)
    return (
      <Box flexDirection="column">
        <Text color="yellow">{`${cards.length} browser choice(s) waiting (/cards)`}</Text>
        {await next(e)}
      </Box>
    )
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text, Button, Input } = $.ui.resolve(e)
    if (!cards.length) return <Text dimColor>No browser choices pending.</Text>
    return (
      <Box flexDirection="column">
        {cards.map(c => (
          <Box key={c.id} flexDirection="column" borderStyle="round">
            <Text bold>{c.question}</Text>
            <Text dimColor>{`from ${c.tool}`}</Text>
            {c.options.map((o, i) => <Button key={`opt:${c.id}:${i}`} onPress={() => void answer($, c, o)}>{o}</Button>)}
            <Button key={`type:${c.id}`} dimColor onPress={() => { typing = typing === c.id ? '' : c.id; $.ui.invalidate('ui.render') }}>
              {typing === c.id ? 'Close prompt bar' : 'Type a reply...'}
            </Button>
            {typing === c.id ? <Input key={`in:${c.id}`} placeholder="message to chat" submitLabel="send" autoFocus onSubmit={v => void answer($, c, v)} /> : null}
          </Box>
        ))}
      </Box>
    )
  })
}
