# Annotated Examples

## Example 1: bloated monorepo audit (default template)

### Input
A 210-line root CLAUDE.md with three review checklists, domain-specific sections for six services, external-only references (Notion, Slack, Confluence), routing to agents that don't exist, and LOC-based planning triggers. One `.claude/rules/frontend.md` exists with 2 lines. Package.json confirms pnpm + turbo + husky.

Fixture: `fixtures/bloated-monorepo/`

### Output

```markdown
# Verdict
The root CLAUDE.md is a 210-line dumping ground. Three review checklists (~80 lines) and six domain-specific sections (~60 lines) consume always-on context that should be conditional. Five external-only references point to resources Claude cannot access. Fix the review-only misplacement and stale external references first.

Grade: C — major cleanup needed

## Top findings
| Severity | Problem | Why it matters | Action |
| --- | --- | --- | --- |
| major | Review checklists in always-on memory | ~80 lines of review-only content loaded every session | Move all three review checklists (Frontend, Admin, API) from root CLAUDE.md into a new REVIEW.md; add a one-line pointer in root |
| major | Service-specific sections in root | Worker, DB, infra, deploy sections only matter when touching those paths | Move each section into a per-service rule file (e.g., `.claude/rules/worker.md`, `services/api/CLAUDE.md`) |
| major | References to tools Claude cannot access | Notion, Slack, Confluence, Postman — Claude has no access to any of these | Delete these lines, or replace with pointers to checked-in docs (e.g., OpenAPI spec instead of Postman) |
| major | Routing to agents that don't exist | CLAUDE.md references ui-subagent and api-subagent but no `.claude/agents/` directory exists | Remove the routing lines unless `.claude/agents/` definitions are added |
| minor | LOC-based planning trigger | "Over 100 lines → plan" fires on file size instead of actual risk | Rewrite: plan when requirements are ambiguous, changes are irreversible, or blast radius is large |

## Recommended changes
1. Move all three review checklists into `REVIEW.md`. Add one routing line in root: "See REVIEW.md for code review checklists." (~80 lines saved from always-on context)
2. Move service-specific sections into per-service rule files or nested CLAUDE.md files near the code they govern. (~60 lines saved)
3. Delete references to Notion, Slack, Confluence, and Postman that Claude cannot access. Replace with checked-in equivalents where they exist.
4. Remove the ui-subagent and api-subagent routing lines unless `.claude/agents/` definitions are created.
5. Rewrite planning trigger: "Plan when requirements are ambiguous, changes touch multiple services, actions are irreversible, or blast radius is large."

## Open questions
- Does the real repo have husky pre-commit hooks? If so, "run lint before commit" is redundant prose.
- Are the subagents actually configured somewhere? If so, create .claude/agents/ definitions.
```

## Example 2: contradiction debug

### Input
A CLAUDE.md that says `yarn test` with Jest. Package.json declares `pnpm@9.0.0` with vitest. A `.claude/rules/testing.md` says "Always use pnpm" and "Never use Jest — migrated to vitest in Q1 2024."

Fixture: `fixtures/contradiction/`

### Output

```markdown
# Verdict
The harness contains direct contradictions. Fix these before any cosmetic cleanup.

Grade: F — actively misleading

## Contradictions
| Surface | Conflict | Canonical fix |
| --- | --- | --- |
| CLAUDE.md vs package.json vs rules/testing.md | Root says yarn; manifest declares pnpm@9.0.0; rules say "always use pnpm" | Rewrite root commands to use pnpm |
| CLAUDE.md vs package.json vs rules/testing.md | Root says Jest; manifest has vitest in devDeps; rules say "never use Jest" | Rewrite root testing section to reference vitest |
| CLAUDE.md vs package.json | Root omits test:e2e (playwright) and typecheck (tsc --noEmit) | Add missing verification commands |

## Corrected snippet
## Commands
- `pnpm install` — install dependencies
- `pnpm dev` — start dev server
- `pnpm test` — run unit tests (vitest)
- `pnpm test:e2e` — run e2e tests (playwright)
- `pnpm typecheck` — type-check the project
- `pnpm lint` — lint
- `pnpm build` — build (run before PR)

## Testing
- Use vitest for unit tests and playwright for e2e tests.
- Before every PR: `pnpm test && pnpm test:e2e && pnpm typecheck && pnpm lint`

## Follow-up
- Delete the generic "General" section (write clean code, meaningful names — zero signal).
- Rewrite planning trigger from "50 lines" to risk-based criteria.
- Verify whether eslint-config-next replaced Airbnb — likely another stale reference.
```

## Example 3: new project bootstrap

### Input
A project with `backend/pyproject.toml` (Poetry, FastAPI, pytest, ruff, mypy) and `frontend/package.json` (pnpm, React, Vite, vitest, eslint). No CLAUDE.md, no .claude/ directory.

Fixture: `fixtures/empty-bootstrap/`

### Output

```markdown
# Verdict
This repo does not yet have a trustworthy instruction harness. The right first step is a minimal root CLAUDE.md.

## Proposed root CLAUDE.md
# CLAUDE.md

## Project
TaskFlow — Python FastAPI backend + React TypeScript frontend.

## Structure
- `backend/` — Python 3.12, FastAPI, SQLAlchemy, Alembic. Managed by Poetry.
- `frontend/` — React 18, TypeScript, Vite, Tailwind. Managed by pnpm.

## Commands
Derive commands from the manifests. Do not guess or fabricate.

### Backend (from backend/)
- `poetry run pytest` — run tests
- `poetry run ruff check .` — lint
- `poetry run mypy .` — type-check

### Frontend (from frontend/)
- `pnpm test` — run tests (vitest)
- `pnpm lint` — lint (eslint)
- `pnpm build` — build (tsc + vite)

## Verification
After changes, run the narrowest check that covers the change:
- Backend only: `poetry run ruff check . && poetry run mypy . && poetry run pytest`
- Frontend only: `pnpm lint && pnpm build && pnpm test`
- Both: run both sets.

## Planning
Plan when: ambiguous requirements, cross-stack changes, database migrations, or hard-to-reverse actions.

## Why this is enough for now
- Both stacks have concrete verification paths derived from manifests.
- No scoped rules, nested CLAUDE.md, or additional surfaces are justified yet.
- When the project grows, add surfaces as needed — not before.

## Open questions
- Backend uvicorn entry point is unknown — add to commands when app structure is established.
- No Alembic config found yet — add migration workflow when it exists.
```
