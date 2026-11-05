---
name: drunken-master
description: Recover what the user meant when a message arrived garbled (speech-to-text, autocorrect, swipe typing, OCR, wrong keyboard layout) or dictated with fillers. Use when a word does not fit its neighbours, sounds like a project term ("sever" for server, "Jane" for Jev), is a nonsense cluster, or the sentence makes sense after swapping 1-3 words, even if the user never mentions typos.
---
# Drunken master: Stage 0 readback

Act on the literal text and you do the wrong thing. Silently "getting the gist" guesses where the user cannot see it. So: repair explicitly, show it first.

## 1. Mark suspects
Words that disagree with neighbours, sound like a term or name from context, are not words, or are real words from the wrong topic. None marked: the message is clean; say nothing. Never touch code in backticks or fences, paths, URLs, `@mentions`, pastes or `[Image #N]` placeholders; they pass through exactly.

## 2. Check distortion classes (most frequent first)
| Class | Examples |
|---|---|
| ASR real-but-wrong word | "sever" for server, "pee are" for PR, "sea eye" for CI, "stagging" for staging |
| Phonetic distortion of a term | "ingratiation tests" for integration tests, "cubernetes" |
| Split or merge | "de bug" for debug, "alot" |
| Wrong script or transliteration | "Jane" for Jev |
| Autocorrect or swipe junk | "asdgh" |
| Wrong keyboard layout | QWERTY typed on the other layout. Map key for key; a junk word that decodes to a real word is the reading, 0.95 |

Say the word aloud; the right one is often audible. Candidates come from project, module, person and tool names in context and terms the user already used.

## 3. Compose 1-3 complete readings
Change only what is garbled. Punctuation, order, tone, profanity stay. Give each a confidence, summing near 1; two equal readings are 0.5/0.5. Check word by word: nothing dropped, reordered or added.

Dictation cleanup (voice input only): drop fillers ("um", "like", false starts), apply mid-sentence corrections ("no wait, the other file"), fix punctuation. Keep their words, order and tone; never answer or resolve what they said. Under 4 words: leave as is.

## 4. Act or ask
Rule without exceptions: if you changed even one word in your head, your first text is `Read as: "..."` (substitutions in bold), before any tool call.
- Top reading 0.75 or more: show the line, then act.
- Leads to something irreversible or costly (deploy, delete, send, pay): act only at 0.9 or more and only if the garbled word does not change what is done. Otherwise ask.
- Below the bar: show the numbered options plus "none of these" and wait. Exception: if all readings produce the same reply, say `Read as`, answer, mention the alternative in a phrase.

## 5. Record
If a `record_interpretation` tool exists, call it with the readings and again with `chosen`. Otherwise skip.

## Never
Improve the user's text. Turn an unfamiliar proper name into a familiar one (if it was in context it is correct). Call external spellcheckers. Answer or use tools before showing the reading.
