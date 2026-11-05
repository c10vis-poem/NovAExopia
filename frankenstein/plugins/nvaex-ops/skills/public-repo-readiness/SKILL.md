---
name: public-repo-readiness
description: Use when the user asks to "make this repo public ready", "publicize the repo", "genericize the repo", "public-ready check", or any similar request to audit a codebase before open-sourcing or public exposure. Audits for secrets, PII, internal infrastructure references, and licensing issues, then produces a remediation plan for user approval.
---

# Public Repo Readiness Audit

## Overview

Systematically audit a codebase for anything that should not be in a public repository. Then write a remediation plan, get approval, and execute it in a fresh context.

**Workflow: Tool check → Fingerprint → EnterPlanMode → Scan → Interview → Plan → /clear → implement in fresh context**

**Never modify files during the audit phase. Find and report first.**

**Readiness ≠ flipping visibility.** Phrases like “make this repo public ready,” “publicize the repo,” or “prepare to open-source” mean audit and remediate content. They do **not** authorize changing the GitHub (or other host) repository from private to public. That flip requires an **explicit yes or no** in the final interview — never assume, never default to yes, never put a visibility change in the plan without an affirmative answer.

---

## Pre-Plan Phase A: Tool Check & Install Interview

Run before entering plan mode. Check which tools are available:

```bash
echo "=== Secret Scanners ===" && which gitleaks trufflehog 2>/dev/null || echo "not found"
echo "=== License Tools ===" && which pip-licenses go-licenses 2>/dev/null || echo "not found"
echo "=== Package Managers ===" && which npm pip3 go cargo 2>/dev/null || echo "not found"
```

For each missing tool that applies to this repo, ask the user in **one consolidated prompt**:

```
The following tools are missing and recommended for a thorough audit:

  [ ] gitleaks     — fast secret scanner, checks full git history
  [ ] trufflehog   — deep secret scanner, VERIFIES if credentials are still active
  [ ] pip-licenses — Python dependency license audit  (only if requirements.txt/pyproject.toml present)
  [ ] go-licenses  — Go dependency license audit      (only if go.mod present)

Should I install any of these? (yes to all / pick specific ones / skip)
```

Install approved tools:
```bash
# gitleaks
curl -sSfL https://raw.githubusercontent.com/gitleaks/gitleaks/master/scripts/install.sh | sh -s -- -b /usr/local/bin
# trufflehog
curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sh -s -- -b /usr/local/bin
# pip-licenses
pip install pip-licenses
# go-licenses
go install github.com/google/go-licenses@latest
```

Note which tools were installed vs. skipped. Mark any skipped scans as "UNVERIFIED — tool not available."

---

## Pre-Plan Phase B: Auto-Detect Internal Fingerprint

Run before entering plan mode. **Do not ask the user** — infer from the environment:

```bash
# Local machine identity
hostname
hostname -f 2>/dev/null
hostname -d 2>/dev/null

# Network interfaces → actual internal subnets
ip addr show | grep "inet " | awk '{print $2}'

# /etc/hosts → explicit internal hostname mappings
grep -v "^#\|^$\|localhost\|127\.0\|::1\|fe80" /etc/hosts

# SSH config → known internal hosts
grep -iE "^Host |^HostName " ~/.ssh/config 2>/dev/null | grep -v "\*"

# Git identity in this repo
git -C . config --list 2>/dev/null | grep -E "remote\.|user\."
git log --all --format="%ae %an" 2>/dev/null | sort -u | head -20

# Remote host visibility (GitHub via gh; do not change anything)
git remote get-url origin 2>/dev/null
gh repo view --json nameWithOwner,isPrivate,visibility 2>/dev/null || echo "gh visibility: unavailable"

# Docker service names
find . \( -name "docker-compose*.yml" -o -name "docker-compose*.yaml" \) 2>/dev/null \
  | xargs grep -hE "^  [a-z_-]+:" 2>/dev/null | awk '{print $1}' | tr -d ':' | sort -u
```

Build the fingerprint:
- **`INTERNAL_NAMES`** = hostname short + /etc/hosts names + SSH Host entries + docker service names
- **`INTERNAL_SUBNETS`** = all RFC1918 defaults + subnets from `ip addr`
- **`INTERNAL_DOMAINS`** = domain from `hostname -d/f` + any `.local/.internal/.home/.lab/.arpa` from /etc/hosts
- **`REPO_VISIBILITY`** = from `gh repo view` when available (`PRIVATE` / `PUBLIC` / unknown); record `nameWithOwner`

---

## EnterPlanMode

**Enter plan mode now.** All scanning, finding compilation, and plan writing happen in plan mode.

---

## Scan Phase 1: Secret & Credential Scanning

### 1a. Git History

```bash
# TruffleHog first — verifies if leaked creds are STILL ACTIVE
trufflehog git file://. --json 2>/dev/null | tee /tmp/trufflehog-report.json

# Gitleaks — broader pattern coverage, structured report
gitleaks detect --source . --report-format json --report-path /tmp/gitleaks-report.json 2>&1

# Fallback: manual history inspection
git log --all --oneline | head -50
git log --all --diff-filter=D --name-only --format="" | sort -u   # deleted files
git stash list
git reflog | head -20
```

**Per finding: state whether the file is tracked/committed (needs history rewrite) or untracked (needs gitignore only).**

### 1b. Working Tree

```bash
EXCLUDE="--exclude-dir=node_modules --exclude-dir=vendor --exclude-dir=.git --exclude-dir=venv --exclude-dir=__pycache__ --exclude-dir=dist --exclude-dir=build"
REPO="."

# Generic secrets
grep -rn $EXCLUDE -E "(password|passwd|secret|token|api_key|apikey|api-key|auth_token|access_token|private_key|client_secret)\s*[=:]\s*['\"][^'\"]{6,}" $REPO 2>/dev/null

# Service-specific formats
grep -rn $EXCLUDE -E "AKIA[0-9A-Z]{16}" $REPO                                      # AWS
grep -rn $EXCLUDE -E "sk_(live|test)_[0-9a-zA-Z]{24}" $REPO                        # Stripe
grep -rn $EXCLUDE -E "xox[baprs]-[0-9]{12}-[0-9]{12}" $REPO                        # Slack
grep -rn $EXCLUDE -E "ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82}" $REPO       # GitHub PAT
grep -rn $EXCLUDE -E "-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY" $REPO        # Private keys
grep -rn $EXCLUDE -E "eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}" $REPO             # JWT

# DB connection strings
grep -rn $EXCLUDE -E "(postgresql|mysql|mongodb|redis|sqlite)://[^@]+@[^/\s]+" $REPO

# Sensitive files that shouldn't be committed
find $REPO -name ".env*" ! -name ".env.example" ! -name ".env.sample" 2>/dev/null
find $REPO \( -name "*.pem" -o -name "*.key" -o -name "*.p12" -o -name "id_rsa" -o -name "id_ed25519" \) 2>/dev/null
find $REPO \( -name "*.sqlite" -o -name "*.db" \) 2>/dev/null
```

---

## Scan Phase 2: PII & Internal Infrastructure

```bash
# Email addresses in code (exclude obvious non-personal)
grep -rn $EXCLUDE -E "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" $REPO \
  --include="*.{js,ts,py,go,rb,java,sh,yaml,yml,json,toml,md,txt,cfg,conf,ini}" 2>/dev/null \
  | grep -v "example\.com\|@types\|noreply\|github\.com\|placeholder"

# Email addresses and names in git commit history
git log --all --format="%ae %ce %an %cn" | sort -u

# Internal IPs — RFC1918 + subnets from INTERNAL_SUBNETS fingerprint
grep -rn $EXCLUDE -E "((10|172\.(1[6-9]|2[0-9]|3[01])|192\.168)\.[0-9]{1,3}\.[0-9]{1,3})" $REPO 2>/dev/null
grep -rn $EXCLUDE -E "169\.254\.[0-9]{1,3}\.[0-9]{1,3}" $REPO 2>/dev/null  # cloud metadata

# Internal hostnames from INTERNAL_NAMES fingerprint (build grep pattern from detected names)
# e.g.: grep -rn -i "webserver1\|db-primary\|ci-runner" $REPO

# Internal domain patterns — standard + INTERNAL_DOMAINS fingerprint
grep -rn $EXCLUDE -E "\.(internal|local|corp|lan|lab|home|arpa|intranet|private)\b" $REPO 2>/dev/null

# Internal URLs
grep -rn $EXCLUDE -E "https?://[a-zA-Z0-9-]+\.(internal|local|corp|lan|home|lab|arpa)" $REPO 2>/dev/null
grep -rn $EXCLUDE -E "https?://[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" $REPO 2>/dev/null

# Private Docker registries
grep -rn $EXCLUDE -E "[a-z0-9.-]+:[0-9]{4,5}/[a-z0-9._/-]+" $REPO 2>/dev/null
```

---

## Scan Phase 3: License Audit

```bash
# LICENSE file
ls $REPO/LICENSE $REPO/LICENSE.md $REPO/LICENSE.txt 2>/dev/null || echo "NO LICENSE FILE"

# Copyright headers
grep -rn $EXCLUDE -i "copyright\|all rights reserved" $REPO \
  --include="*.{js,ts,py,go,rb,java}" 2>/dev/null | head -20

# Dependency license audit (run whichever applies)
[ -f package.json ]    && npx license-checker --summary 2>/dev/null
[ -f requirements.txt ] || [ -f pyproject.toml ] && pip-licenses 2>/dev/null
[ -f go.mod ]          && go-licenses report . 2>/dev/null
[ -f Cargo.toml ]      && cargo license 2>/dev/null
# Flag any GPL/AGPL/LGPL results — these are copyleft and may restrict how you can license the repo
```

---

## Final Interview (still in plan mode)

After completing all scans, ask the user in **one consolidated prompt** covering any open decisions:

```
Scan complete. Before I write the remediation plan, I need a few decisions:

1. LICENSE: No LICENSE file found. Which license do you want?
   (MIT / Apache 2.0 / GPL-3.0 / other)

2. GIT HISTORY REWRITE: [X] secrets found in committed history.
   Rewriting history is destructive and requires coordinating with all collaborators.
   Proceed with history rewrite plan? (yes / no / I'll handle manually)

3. AUTHOR IDENTITY: Personal name and/or email would ship with this repo if published as-is.

   Working tree (examples):
   - LICENSE — "Jane Doe"
   - package metadata / plugin.json — Jane Doe <jane@example.com>

   Commit history (author/committer on N commits):
   - Jane Doe <jane@example.com>

   GitHub can attribute commits to your account without publishing a personal
   email, via a noreply address such as:
     12345678+youruser@users.noreply.github.com
     (or youruser@users.noreply.github.com)

   How should we handle identity before publish?
   a) Rewrite commits and files to GitHub noreply (optional display name)
   b) Files only — leave commit history as-is
   c) Commits only — leave file contents as-is
   d) Keep personal identity public (no change)

4. REPOSITORY VISIBILITY: Remote is currently [PRIVATE | PUBLIC | unknown]
   ([owner/repo] on GitHub, or note if not a gh remote).

   Making the *codebase* public-ready is separate from making the *GitHub
   repository* public. Do not treat “public ready” / “publicize” / “open-source”
   as permission to change visibility.

   After remediation, should the plan include flipping this repository to public?
   a) Yes — final step only, after all other remediation (and force-push if any)
   b) No — leave visibility unchanged; readiness work only

   (Require an explicit a or b. If the answer is unclear, omit, or deferred —
   treat as No. Never default to Yes.)

5. SCOPE: These items are borderline — include in remediation or leave?
   - [list any MEDIUM/LOW items that need judgment]
```

Only ask about decisions that are actually needed based on findings. Skip questions with obvious answers.

**When to include question 3:** If Scan Phase 2 (or fingerprint git identity) found a real personal name and/or a non-noreply personal/work email in the working tree **or** in commit author/committer fields. Skip if identity is already username-only + `*@users.noreply.github.com`, or is clearly a project/org bot identity the user intends to keep.

**When to include question 4:** Always when a hosting remote exists and visibility is not already public. If already **public**, skip the flip question and note in the plan: “Repository is already public — no visibility change.” If `gh` cannot determine visibility, still ask and report “unknown (could not query).”

---

## Write Remediation Plan

Write the plan to a file: `./public-repo-remediation-plan.md`

Structure:

```markdown
# Public Repo Remediation Plan

## Auto-Detected Internal Fingerprint
- Hostnames: [list]
- Subnets: [list]
- Domains: [list]
- Git identity: [emails/names found in commits]
- Repo visibility: [PRIVATE/PUBLIC/unknown] — [owner/repo or n/a]
- Visibility flip approved: [yes / no / n/a already public]
⚠️ If incomplete, add missing names and re-run.

## Findings Summary
| Severity | Count |
|----------|-------|
| CRITICAL | X |
| HIGH     | X |
| MEDIUM   | X |
| LOW      | X |

## CRITICAL Findings
- `file:line` — description — tracked/untracked

## HIGH Findings
...

## Remediation Tasks

### Task 1: Rotate All Exposed Credentials (IMMEDIATE — before any other step)
Assume all found credentials are compromised. Rotate NOW.
- [credential] in [file] — rotate at [service URL]

### Task 2: Remove Secrets from Working Tree
- [specific file edits with before/after]
- Add to .gitignore: [list]

### Task 3: Git History Rewrite (if applicable)
⚠️ DESTRUCTIVE — coordinate with all collaborators first
- git filter-repo --path <file> --invert-paths
- Force-push all branches after rewrite
- Invalidate any clones/forks

### Task 4: Author Identity Anonymization (if approved)
- Resolve target identity:
  - Prefer `$(gh api user --jq '.id')+$(gh api user --jq '.login')@users.noreply.github.com`
  - Fallback: `$(gh api user --jq '.login')@users.noreply.github.com`
  - Display name: GitHub login, or a name the user chose
- Working tree: replace personal name/email in LICENSE, package metadata, plugin manifests, etc. (only where user approved)
- History (if approved): rewrite author/committer with git-filter-repo, e.g.:
  ```bash
  git filter-repo --force \
    --name-callback 'return b"YOUR_DISPLAY_NAME"' \
    --email-callback 'return b"ID+user@users.noreply.github.com"'
  ```
  Or map only specific identities with `--email-mapping` / `--name-mapping` files.
- After any history rewrite, **scrub old commits and refs** so personal identity cannot be recovered from the local object store:
  ```bash
  rm -rf .git/refs/original/
  git reflog expire --expire=now --all
  git gc --prune=now --aggressive
  ```
  Verify: `git log --all --format='%an <%ae> | %cn <%ce>' | sort -u` shows only the approved identity.
- Force-push rewritten branches/tags; tell collaborators to re-clone.

### Task 5: Remove/Replace Internal References
- [file:line] — replace "[internal value]" with "[generic placeholder]"

### Task 6: Add LICENSE File
- Create LICENSE with [chosen license] text

### Task 7: Dependency License Cleanup (if needed)
- [specific dependency] — [issue] — [resolution]

### Task 8: Flip repository visibility to public (ONLY if user chose Yes on question 4)
⚠️ Do **not** include this task unless the interview answer was an explicit Yes.
If No, unknown, or not asked because already public: omit this task entirely (do not list it as skipped optional work that an executor might “helpfully” do).

- Prerequisites: all prior remediation tasks done; history rewrite force-pushed if applicable; optional re-scan clean
- Command (GitHub): `gh repo edit OWNER/REPO --visibility public --accept-visibility-change-consequences`
- Verify: `gh repo view OWNER/REPO --json visibility,isPrivate`
- If the host is not GitHub, describe the equivalent UI/API step — still only when Yes was explicit

## Scan Limitations
- Tools not available: [list]
- Items not checked: binary files, [other]
- Fingerprint may be incomplete: [note if confidence is low]
```

---

## ExitPlanMode

Exit plan mode and present the plan for user approval.

---

## After Approval: Execute

Tell the user:

> "Plan saved to `./public-repo-remediation-plan.md`. Use `/clear` then tell me to implement the plan from that file in a fresh context."

---

## Key Rules

1. **Audit first — never modify files during scanning**
2. **All found credentials must be rotated immediately** — assume compromised whether or not the repo is already public
3. **Git history rewrite is destructive** — flag prominently, get explicit confirmation
4. **Report the auto-detected fingerprint** so the user can verify it's complete
5. **Per finding, state tracked vs. untracked** — this determines whether history rewrite is needed
6. **Never flip private → public without an explicit Yes** — “public ready” / “publicize” / “open-source this” are not consent to change host visibility. No = leave private. Unclear = No. Do not put a visibility-change task in the plan unless Yes.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Only scanning working tree | Always check git history — deleted secrets persist |
| No tool scan | Grep misses service-specific patterns; use gitleaks + trufflehog |
| Rotating credentials after pushing | Rotate on discovery, before any push |
| Forgetting stash and reflog | Check `git stash list` and `git reflog` |
| History rewrite without scrubbing refs | After filter-repo: drop `refs/original`, expire reflog, `git gc --prune=now` |
| Shipping personal email in commits | Offer GitHub noreply rewrite before publish |
| Assuming user wants the repo made public | Ask visibility Yes/No; omit flip task unless explicit Yes |
| Putting visibility flip mid-plan | If approved, last step only — after cleanup and any force-push |
| Missing transitive dependency licenses | Run `license-checker --summary`, not manual review |
| Scanning node_modules/vendor | Exclude — not your code |
| Not distinguishing tracked vs. untracked | Committed secrets need history rewrite; untracked need gitignore |
