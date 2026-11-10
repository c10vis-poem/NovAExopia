#!/usr/bin/env sh
# Vendor tools/plugin-shared/ into this package (self-contained hot-swap).
here="$(cd "$(dirname "$0")/.." && pwd)"
cp "$here/../../tools/plugin-shared/killswitch.sh" "$here/scripts/killswitch.sh"
