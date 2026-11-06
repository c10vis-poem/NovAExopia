#!/usr/bin/env bash
# Rule 4, PreToolUse (Bash, Edit, Write): the agent cannot change settings, enforcement state or the switches.
. "$(dirname "$(realpath "$0")")/lib/parts.sh"
run_parts settings-guard state-guard
