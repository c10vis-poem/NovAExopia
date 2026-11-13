#!/usr/bin/env sh
# Every hook of every plugin, three bad inputs, exit 0 and nothing on the owner's screen. See hooks_quiet.py.
exec python3 -I "$(dirname "$0")/hooks_quiet.py" "$@"
