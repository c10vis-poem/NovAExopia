#!/usr/bin/env bash
# Setup script for a Claude Code on the web environment: paste into the environment's "Setup script" box at
# claude.ai/code. Cloud sessions do not install the plugins a repo enables in .claude/settings.json (Claude Code docs,
# cloud environments), so this registers the marketplaces from GitHub and installs every plugin.
# Keys for outside services (PERPLEXITY_API_KEY, GEMINI_API_KEY, HF_TOKEN, TYPESAFE_API_KEY) go in the
# environment's variables, never here. Needs network access that reaches github.com.
set -u
mk() { claude plugin marketplace add "$1" >/dev/null 2>&1 && echo "marketplace $1" || echo "marketplace $1 FAILED"; }
in() { claude plugin install "$1" --scope user >/dev/null 2>&1 && echo "installed $1" || echo "install $1 FAILED"; }
mk c10vis-poem/Aesop-Xi        # marketplace aesop-xi: the rules and hooks
mk c10vis-poem/NovAExopia      # marketplace novaexopia: tools, agents, MCP servers
mk c10vis-poem/NovAExorpus     # marketplace nvaex-vault: greedy-crane
in aesops-enforcements@aesop-xi
for p in nvaex-jev-core nvaex-memory nvaex-rea-forge nvaex-burn claw-mcp nvaex-ui-cockpit; do in "$p@novaexopia"; done
in greedy-crane@nvaex-vault
claude plugin list 2>&1 | grep -cE 'enabled' | sed 's/^/plugins enabled: /'
