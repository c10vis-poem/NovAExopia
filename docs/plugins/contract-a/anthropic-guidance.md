# Anthropic guidance used by contract A (fetched 2026-11-11)

Every quote below came back from WebFetch this session. Sources:
H = https://code.claude.com/docs/en/hooks, S = https://code.claude.com/docs/en/skills,
M = https://code.claude.com/docs/en/memory, SL = https://code.claude.com/docs/en/statusline,
CE = https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

## Hook output: what costs context and what does not
- additionalContext enters the model: "The `additionalContext` field passes a string from your hook into Claude's
  context window. Claude Code wraps the string in a system reminder ... it doesn't appear as a chat message" (H).
- systemMessage is for the user: "Warning message shown to the user" (H); "To surface a message to the user on any
  platform, return `systemMessage` in JSON output" (H).
- Cap: "`additionalContext`, `systemMessage` ... and its plain stdout, are capped at 10,000 characters" (H).
- Static text belongs elsewhere: "For instructions that never change, prefer CLAUDE.md. It loads without running a
  script" (H).
- Tone: "Write the text as factual statements rather than imperative system instructions ... Text framed as
  out-of-band system commands can trigger Claude's prompt-injection defenses" (H).
- Stop: "Stop and SubagentStop also accept `hookSpecificOutput.additionalContext` for non-error feedback that
  continues the conversation" (H).
- MCP identity in PreToolUse: "the input also carries `mcp_server`, an object with the server's `name` and a
  `source` ... Base trust decisions on `source` rather than on `name` or the `mcp__<server>__` tool-name prefix"
  (H). Plugin tools are named "`mcp__plugin_<plugin-name>_<server-name>__<tool>`"; the hook-config form is
  "`plugin:<plugin-name>:<server-name>`" (H). So a contract's `Server:` value must be matched against both the
  tool-name segment and `mcp_server.name` (recon false alarm 2).
- PostToolUseFailure "Runs when a tool that started executing fails" (H): a grep with no match counts, so the
  research-on-failure note fires on harmless exits.

## Status line: the zero-context display
- "The status line runs locally and does not consume API tokens" (SL).
- Configured by `"statusLine": {"type": "command", "command": "...", "padding": 2}` in user or project settings;
  optional `refreshInterval` (SL).
- Runs "once when a session starts", then "when a new assistant message arrives", after `/compact`, on
  permission-mode change, and on the refresh timer (SL). Multi-line output is supported (SL).
- Consequence for C3: persistent notices (unmet lines, breaches, nudges) go to the status line, which costs no
  context and needs no reply. Only what the agent must act on goes to additionalContext or a Stop block.

## Skills: what loads
- "In a regular session, skill descriptions are loaded into context so Claude knows what's available, but full
  skill content only loads when invoked" (S). Default: "Description always in context, full skill loads when
  invoked" (S).
- "the combined `description` and `when_to_use` text is truncated at 1,536 characters in the skill listing" (S).
- Subagents differ: "Subagents with preloaded skills ... the full skill content is injected at startup" (S).
- Name clashes: "Enterprise over personal, and personal over project"; "A plugin skill and a skill at any of the
  locations above | Both load, because plugin skills are namespaced" (S). This is why user copies and plugin
  copies of the same skill both show up.
- Keeping skills out: "`disable-model-invocation: true` ... removes the skill from Claude's context entirely"; or
  `skillOverrides` "off" = "Hidden" (S).
- "Keep `SKILL.md` under 500 lines. Move detailed reference material to separate files" (S).

## Memory files
- "target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence" (M).
- "Imports ... don't reduce its context cost, because imported files load together with the CLAUDE.md that imports
  them" (M). (`@AGENTS.md` in a CLAUDE.md loads it whole.)
- "if two instructions contradict each other, Claude may pick one arbitrarily. Review your CLAUDE.md files ...
  periodically to remove outdated or conflicting instructions" (M); `/doctor prompt-audit` does this check (M).
- "Claude treats them as context, not enforced configuration. To block an action regardless of what Claude
  decides, use a PreToolUse hook" (M).
- Auto memory loads "first 200 lines or 25KB" every session (M).

## Context engineering
- "maintain lightweight identifiers (file paths, stored queries, web links, etc.)" instead of pre-loading (CE).
- "enables progressive disclosure ... Agents can assemble understanding layer by layer, maintaining only what's
  necessary in working memory" (CE).
- "striving for the minimal set of information that fully outlines your expected behavior" (CE).
- "once a tool has been called deep in the message history, why would the agent need to see the raw result
  again?" (CE).
- "CLAUDE.md files are naively dropped into context up front" while "primitives like glob and grep allow it to
  navigate its environment" (CE).

## What this means for the repairs
1. Notices that repeat (Gate 3, JEV route, unmet-line lists, breach counts) move to the status line.
2. Stop blocks carry only what the agent must fix now, as short factual lines.
3. The contract's `Server:` match accepts both name forms.
4. Context loading: one index read on demand beats a list loaded every prompt (see context-loading.md).
