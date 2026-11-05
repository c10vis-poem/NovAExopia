---
name: gemini-genai
description: Call Gemini or OpenRouter models, and get a second opinion, through claw.infer. Use for cross-model checks and bulk drafting.
---
`claw.infer provider=gemini model=gemini-2.5-flash prompt=...` (key `GEMINI_API_KEY`) or `provider=openrouter model=<id>` (key `OPENROUTER_API_KEY`). Keys come from the environment only.

Second opinion (consensus): call twice with different providers/models and the same prompt, then compare answers; state disagreements instead of averaging them.

Not folded: Vertex auth, streaming, multimodal input. Donors `c10vis-poem/Merovin-genai-for-developers-` and `NxAEx-gemini-skills` are not on this phone (find over ~/repos, ~/.claude/plugins, ~/local-plugins found none), so nothing was taken from them.
