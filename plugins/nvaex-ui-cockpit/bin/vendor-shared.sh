#!/usr/bin/env sh
# Copy the shared kill switch into this package (hot-swap rule 1).
here=$(cd "$(dirname "$0")/.." && pwd)
cp "$here/../../shared/killswitch.sh" "$here/scripts/killswitch.sh" && chmod +x "$here/scripts/killswitch.sh"
