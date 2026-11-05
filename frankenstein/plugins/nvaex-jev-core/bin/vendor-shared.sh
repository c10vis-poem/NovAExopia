#!/usr/bin/env sh
# Vendor frankenstein/shared/ into this package (self-contained hot-swap).
here="$(cd "$(dirname "$0")/.." && pwd)"
cp "$here/../../shared/killswitch.sh" "$here/scripts/killswitch.sh"
