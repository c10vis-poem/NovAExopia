#!/usr/bin/env sh
# Build the Kotlin server on a machine with gradle + JDK 17+. UNTESTED on device.
# Output: kotlin/build/libs/claw-mcp-all.jar (bin/claw-mcp prefers it over the Python shim).
set -e
cd "$(dirname "$0")/../kotlin"
command -v java >/dev/null || { echo "need a JDK 17+ (pkg install openjdk-21)"; exit 1; }
command -v gradle >/dev/null || { echo "need gradle (pkg install gradle) or run on the VM and copy the jar"; exit 1; }
gradle --no-daemon shadowJar
