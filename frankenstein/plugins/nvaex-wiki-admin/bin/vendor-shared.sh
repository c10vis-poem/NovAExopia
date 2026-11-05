#!/usr/bin/env sh
# Copy frankenstein/shared/killswitch.sh into this package (hot-swap: package stays self-contained).
here=$(cd "$(dirname "$0")/.." && pwd)
cp "$here/../../shared/killswitch.sh" "$here/scripts/killswitch.sh" && chmod +x "$here/scripts/killswitch.sh" && echo "vendored killswitch.sh"
