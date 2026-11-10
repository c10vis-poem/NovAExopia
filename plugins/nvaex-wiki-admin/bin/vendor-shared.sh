#!/usr/bin/env sh
# Copy tools/plugin-shared/killswitch.sh into this package (hot-swap: package stays self-contained).
here=$(cd "$(dirname "$0")/.." && pwd)
cp "$here/../../tools/plugin-shared/killswitch.sh" "$here/scripts/killswitch.sh" && chmod +x "$here/scripts/killswitch.sh" && echo "vendored killswitch.sh"
