---
name: ccfind
description: "Search the user's own past Claude Code sessions by content and report which conversation discussed a thing, when, in which project, and how to resume it. Use this whenever the user asks about something from an earlier session rather than the current one - \"where did we\", \"which session was that\", \"we already fixed this\", \"what was that command\", \"did I ask about X before\", \"find the conversation about\", \"remind me how we solved\", \"search my history\" - or invokes /ccfind. The same asks in any other language fire it too: the trigger is what the user wants, not the words they used, and most users type these in their own language. Ranks whole transcripts with BM25 over prompts, answers, reasoning, tool calls and tool output, so an exact identifier, an error string, or a vague paraphrase all work. Runs entirely on local files with no API calls and no network."
---

# ccfind

Full-text search over the local transcripts in `~/.claude/projects/`.

This skill is user-invocable: `/ccfind:ccfind <query>` runs it with the query as
the arguments, so there is no separate slash command to keep in step with it.

`--resume` matches a session by id or name only, and `/insights` writes a report
rather than answering a question. Neither one finds the session where a specific
thing was discussed. This does.

## How to run it

Everything happens in one Node process. Two commands, in this order, as **two
separate tool calls** - never chained with `&&` into one. `search` reports which
model is asking by reading the session transcript, and on the first turn of a
fresh session that file only has the earlier call's entries in it: chaining the
two hides the very thing that decides the layout (see `client` under "Reading a
hit"), and the answer comes out in the wrong shape.

```bash
node <skill-dir>/scripts/ccfind.mjs index
node <skill-dir>/scripts/ccfind.mjs search "<query>" --limit 12 --lang <en|ru> --json
node <skill-dir>/scripts/ccfind.mjs show <session-id> --json      # one session's turns
node <skill-dir>/scripts/ccfind.mjs open <session-id>             # new window on it
```

`pick "<query>"` also exists: an arrow-key list that runs `claude --resume` on
Enter, with `/` to narrow the query in place. It needs a real terminal, so **never run it yourself** - a tool call has no
tty and it would just print the list. Suggest it to the user instead - and check
`command -v ccfind` before you do. Without a launcher their shell answers
`bash: ccfind: command not found` (`zsh: command not found: ccfind` on macOS),
which reads like a broken plugin rather than a missing one-time step, so say it in the same breath as the suggestion and offer
`install`: it writes one launcher onto their PATH and `uninstall` removes it. Run
`install` when they ask for a terminal command or take that offer, never on your
own initiative - it writes outside the plugin directory.


If either command fails with `node: command not found`, stop and tell the user
that ccfind needs Node 18+ on `PATH` and that Claude Code's native installer
does not provide it. Do not fall back to reading transcripts by hand.

`index` is idempotent: it prints `index up to date` and exits when nothing
changed. It is not free. Any change rebuilds the whole corpus at roughly
13 MB/s - a second or two for a small history, about 19 s for 250 MB - and inside
a live session the current transcript is always growing, so that skip rarely
fires and each search pays the rebuild once. Run it before searching anyway, so a
conversation from ten minutes ago is findable; on a large history the call takes
tens of seconds, so say the indexing step is running rather than leaving the user
with a tool call that looks stuck. Then read the JSON from `search` and answer
from it.

## Cost

Indexing and searching are local file I/O plus arithmetic - zero API calls,
zero tokens. The only model work is you reading a small JSON result and writing
a short answer. A `--limit 8 --json` result is a few kilobytes.

**Do not separately Read any `*.jsonl` transcript files.** They are large, and
the snippet in each hit already contains the matching text. If a hit needs more
context, re-run `search` with `--session <id>` and a narrower query, or tell the
user the `resume` command from the hit and let them jump there.

## Query options

| Flag | Effect |
| --- | --- |
| `--limit N` | number of hits (default 10) |
| `--group session\|exchange` | one hit per session (default) or per user turn |
| `--project SUBSTR` | restrict to a project directory or cwd |
| `--session ID` | restrict to one session (id prefix is enough) |
| `--days N` | only sessions touched in the last N days |
| `--field title\|prompt\|answer\|thinking\|tool\|output\|summary` | search only that field |
| `--exclude ID[,ID...]` | drop sessions from results |
| `--self` | allow the current session to appear (it is excluded by default) |
| `--all` | keep the weak matches the relevance gate hides |
| `--lang en\|ru` | language of `rendered` (default: guessed from the query) |
| `--json` | machine-readable output - use this |

`show <id>` takes `--turns N` (default 40) and `--json`. It lists a session's user
turns in order, so a hit can be understood without opening the transcript.

Useful narrowings: `--field prompt` finds where the *user* raised something,
`--field output` finds a command's actual output, `--group exchange` pinpoints
the turn rather than the conversation.

## Reading a hit

```json
{
  "relevant": 4, "weak": 19, "total": 23,
  "hits": [{
    "score": 22.65, "coverage": 1, "chunks": 160, "turns": 14,
    "title": "cluster-setup", "session": "a1b2c3d4-...", "project": "-home-me-infra",
    "cwd": "/home/me/infra", "branch": "main",
    "when": "2026-07-28T06:26:...", "prompt": "registry mirror not picked up by containerd",
    "opening": "bringing up a fresh single-node cluster on 10.0.0.4",
    "field": "tool", "snippet": "...", "resume": "claude --resume a1b2c3d4-..."
  }]
}
```

- `title` is the session's name (`/rename`) or the model-written one; fall back
  to `project` when it is null.
- `prompt` is the user turn the match hangs off - quote it, it is what the user
  will recognise.
- `coverage` is the fraction of the query's words present. `1` means every word
  was found somewhere in that session; a low value means a partial match.
- `field` says where the match landed. `prompt` or `answer` means it was
  discussed; `tool` or `output` means it appeared in a command or its output.
- `opening` is the turn the session *started* from - the cheapest one-line
  description of what it was about. Null when it is the matching turn itself.
- `turns` is how many user turns the session has: a 40-turn session is a project,
  a 2-turn one is a question.
- `open` is `/resume <id>` - typed in this window it switches to that session in
  place. `resume` is `claude --resume <id>`, which starts a separate run instead.
- `rendered` (top level): the finished answer - table, counts line, and the
  top hit's `/resume` line - already laid out and in the language of `lang`.
  This is what the user sees. See "Answering". `renderedCompact` is the same
  answer one line per hit, for the picker's question string.
- `client` (top level, when the search can tell who is asking): `model`, plus a
  `layout` of `table` or `in-question` and a `note` saying what to do. **Follow
  it** - it is measured from the session's own transcript, not guessed. It only
  changes *where* `rendered` goes, never what it says: `table` means the message
  text, `in-question` means this model does not write message text in a turn
  that also calls a tool, so `rendered` rides in the picker's `question`
  instead. See "Letting the user pick". A `layout` of `unknown`, or no `client`
  at all, is handled as `table`.
- `relevant`, `weak` and `total` (top level). BM25 scores every session holding
  a single query word, so `total` is wide and mostly noise. The relevance gate
  keeps the hits scoring within 25% of the top one - `relevant` - and hides the
  rest as `weak`. `hits` therefore never exceeds `relevant`, and the top hit is
  always kept. `--all` returns the whole tail if the user wants the mentions
  themselves.

## Answering

**The answer is `rendered`, pasted verbatim.** The script builds it so that the
answer looks the same whichever model is asking - when each model wrote its own
table, each wrote a different one, and some wrote none. So do not build a table,
do not reword, trim, translate or reorder `rendered`, and do not summarise it in
prose instead. Copy it byte for byte into a fenced block, as the first thing in
the message:

````
```text
<rendered>
```
````

A house style that bans tables or demands compression does not reach it: it is
a code block, and it is the answer, not decoration. No lead-in sentence in front
of it.

Language: pass `--lang` for the language the user writes in - `ru` for Russian,
`en` otherwise - not the language of the query words, which are often English
identifiers inside a Russian question. Without `--lang` the script guesses from
the query's alphabet. For a language it has no labels for, `rendered` comes out
in English - paste it as it is anyway; an identical block beats a hand-made one.

After the block, at most two short lines, in the user's language and in whatever
output style the session runs:

- if the top hit is not the one to open, say which row is and why in one clause,
  and give that row's `open` field on its own line - copied **byte for byte**
  from the JSON, all 36 characters of the id. A truncated id is not something
  the user can type.
- if `coverage` is well below 1 on every hit, or `relevant` is 1 with a large
  `weak`, one line saying the match is thin.

Nothing else: no verdict on the weak ones (the gate measured that), no restating
the counts - `rendered` already carries them. `/resume <id>` is the built-in
slash command that switches this window to that session; `claude --resume` (the
`resume` field) is the terminal variant - mention it only if they are in a
terminal.

## Letting the user pick

The block is text - the user cannot select in it. So end a session search with an
`AskUserQuestion` picker; that is the only arrow-key selection the chat has.

**The picker comes after the block, never instead of it.** Paste `rendered` as
message text, *then* call `AskUserQuestion` in the same turn with a one-line
question. Writing text before a tool call is a deliberate act here, not
narration: the block is the answer. If anything in force makes you unwilling to
send message text ahead of the picker call, resolve it the other way: send the
block as the final message and skip the picker. A picker with nothing above it
is the one outcome that is always wrong.

**Unless `client.layout` is `in-question`.** Then message text next to a tool
call never reaches the user, so the question string carries the answer instead:
`renderedCompact` verbatim at the top of `question`, the one-line ask on the last
line. It is `rendered` with one line per hit and no column alignment, because
the question string is not guaranteed to keep runs of spaces - same rows, same
counts, same `/resume` line. After the pick, answer in
message text as usual - that turn has no tool call in it, so the text survives -
and give the full `/resume` line there.

`AskUserQuestion` takes **four options, hard cap** (harness limit, not ours), so
page through the hits three at a time:

- options 1-3: the next three hits. Label = session title, description = date,
  project, and the `opening` turn.
- option 4: `next 3 (4-6 of 13)`, in the language of the answer - naming the
  range, so the user can see the arrows reach the whole list. Re-ask with the
  next three when they take it. Only on the last page does option 4 become a
  plain *show all N* dump.

If the user cancels the picker, the block is already on screen - that is the
point of printing it first - and it ends in a `/resume` line they can type.

Whatever they pick, run `show <id> --json` and **answer their original question
from it** - not a summary of the session for its own sake. Terse: what that
session concluded about the thing they asked, and where in it that sits. Then
they can keep asking about it here, which is the point: the session's content is
now in this conversation.

Then **open it**, because that is what picking is for. Two things, both:

```bash
node <skill-dir>/scripts/ccfind.mjs open <session-id>
```

`open` launches a new terminal window on that session (`claude --resume`, in the
session's own cwd - tmux window if they are in tmux, iTerm/Terminal on macOS, the
installed emulator on Linux). It returns as soon as the window is up, so it never
holds the tool call open for the life of that window.

**Run it immediately after the pick, without asking.** Not "shall I open a window
on it?" - picking a session *is* the request to open it, and asking costs the
user another turn to say yes. Then one clause saying which window opened.

And still give the last line: **`/resume <full-id>`** - the `open` field
verbatim, all 36 characters, no ellipsis. That is the built-in slash
command; typed in *this* window it switches this conversation to that session
instead of opening a second one. A skill cannot type it for them - no tool
switches the active session - so hand them the line every time. `open` for a new
window, `/resume` to switch here: never end a pick without both. Arrow keys over *every* hit, an incremental filter on `/`, and
Enter that really hands the terminal to `claude --resume` exist in one place
only: `ccfind pick "<query>"` in a terminal. Recommend it when the list is long,
or when the query looks like it needs a couple of tries.

## Notes

- `sidechain: true` marks a subagent transcript rather than the main thread.
- Injected context (system reminders, hook output, slash-command wrappers) is
  stripped before indexing, so hits are on real conversation.
- Images, encrypted advisor payloads, and thinking signatures are not indexed.
- Tool output is indexed up to 16 KB per result; a huge dump is truncated.
- The index lives in `~/.claude/ccfind/` and never leaves the machine. If the
  user sets `CLAUDE_CONFIG_DIR`, both the corpus and the index follow it;
  `CCFIND_CONFIG_DIR` overrides just ccfind.
