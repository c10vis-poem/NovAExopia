---
name: gemini-genai
description: Call Gemini or OpenRouter models via claw.infer. Use for a second opinion, cross-model checks and bulk drafting.
---
`claw.infer provider=gemini model=gemini-3.8-flash prompt=...` (default when `model` is omitted; `gemini-4-argon` for hard reasoning and 1M context) (key `GEMINI_API_KEY`) or `provider=openrouter model=<id>` (key `OPENROUTER_API_KEY`). Keys come from the environment only.

Second opinion (consensus): call twice with different providers/models and the same prompt, then compare answers; state disagreements instead of averaging them.

Model names, SDK use, embeddings, Live API and the Antigravity agent: load this package's `gemini-api-dev` skill (copied from the fork `c10vis-poem/NxAEx-gemini-skills`) before writing or changing any Gemini call; it is the reference and its model list wins over this file. Not folded here: Vertex auth, streaming, multimodal input.
