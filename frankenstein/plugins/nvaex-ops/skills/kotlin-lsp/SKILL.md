---
disable-model-invocation: true
name: kotlin-lsp
description: Check Kotlin (.kt, .kts) in the Android APK repos with what this phone has. Use before editing or committing Kotlin when no compiler or language server is available. Says plainly that LSP is not available here.
---

# kotlin-lsp (no language server on this phone)

Checked 2026-11-05: `kotlin-language-server`, `kotlinc`, `gradle`, `ktlint`, `detekt` are all missing. Java 21 exists. A repo's `gradlew` exists in several repos but needs a Gradle distribution download and the Android SDK, neither present. Nothing here can give type errors, go-to-definition or find-references. Do not claim it does.

What this skill provides is a structural check only.

## Steps
1. `python3 -I scripts/kt_check.py --tools` (path relative to this skill). Prints which tools exist. If `compile/LSP available: yes` appears someday, use that tool instead and ignore the rest.
2. `python3 -I scripts/kt_check.py path/to/File.kt path/to/dir` checks balance of `()[]{}`, strings, raw strings and nested block comments, duplicate `package` lines, and counts `!!`. Exit 1 prints `file:line: message`.
3. Report as "structurally OK, not compiled". Real compile errors only show up in a build on a machine with the Kotlin toolchain (the operator's PC or CI); say so.
4. For code navigation without an LSP use the code-review-graph tools if the agent has them (they parse Kotlin with tree-sitter), or plain `grep -rn`.

Not done and not planned here: installing a language server or Gradle (the operator's call; Kotlin LS needs a JDK plus a Gradle-resolvable project).
