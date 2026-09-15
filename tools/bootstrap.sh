#!/data/data/com.termux/files/usr/bin/bash
# tools/bootstrap.sh — thin wrapper calling aesop-xi's canonical bootstrap.
# See ~/repos/aesop-xi/tools/bootstrap.sh for the full-stack startup logic.
set -euo pipefail

AESOP_XI_ROOT="${AESOP_XI_ROOT:-$HOME/repos/aesop-xi}"
if [ -x "$AESOP_XI_ROOT/tools/bootstrap.sh" ]; then
  bash "$AESOP_XI_ROOT/tools/bootstrap.sh"
else
  echo "[bootstrap] WARN: aesop-xi bootstrap missing at $AESOP_XI_ROOT/tools/bootstrap.sh — skipping stack startup" >&2
fi

# Repo-specific post-boot (add below as needed).
