# Protecting operational consumers

Use this trace to protect files near cleanup candidates. It does not authorize
feature retirement, dependency pruning, or source removal. Ordinary Cut Weight
work targets development residue even when operational code is unreachable.

For optional development tooling, apply the retention decision in
[agent-artifacts.md](agent-artifacts.md) first. Its own hook loading its own code
proves tool functionality, not a requirement to retain that tool. The user can
retire that local setup; include its registrations in the removal plan. When the
repository distributes the plugin as its product, that plugin code remains
protected product source.

An entry point is a file the outside world invokes directly -- an OS, a
runtime, a platform, a CI system, or a human following the README. The
keep-set is everything transitively reachable from these. Getting this list
right matters more than anything downstream, so collect evidence for each
entry point rather than assuming.

Ask three questions of every project:

1. **How is it started?** (start commands, service definitions, README run
   instructions)
2. **What does the platform load?** (manifest-declared files the host
   discovers on its own)
3. **What do CI and deploy run?** (workflows exercise files nothing else
   references)

## Where to look, by ecosystem

### Node / JavaScript

- `package.json`: `main`, `bin`, `exports`, `module`, and every command in
  `scripts` (parse the actual commands -- `"start": "node server.js"` makes
  `server.js` an entry point; test runners make the test glob an entry point).
- `Dockerfile` `CMD`/`ENTRYPOINT`, `Procfile`, `docker-compose.yml` commands.
- CI workflows (`.github/workflows/*.yml`): every script or file they invoke.
- Framework conventions: `next.config.*` implies `pages/`/`app/` are
  platform-loaded; same idea for Nuxt, Remix, Astro, SvelteKit.

### Python

- `pyproject.toml` `[project.scripts]` / `setup.py` `entry_points`.
- `__main__.py`, `manage.py`, `wsgi.py`/`asgi.py`.
- The README: stdlib-server projects are often started with a bare
  `python app/server.py` documented nowhere else.
- Scheduled/service invocations: systemd units, Task Scheduler exports,
  cron lines in docs.

### Static / no-build web (in-browser Babel, vendored libs)

- The HTML files a server serves or a browser opens: every `<script src>`,
  `<link href>`, `<img src>` is an edge.
- JS that fetches more code or assets at runtime: `fetch("...jsx")`,
  dynamic `import()`, worker constructors. Path literals in served JS are
  edges too.
- The server's static-file root: anything under a directory the server
  serves wholesale is reachable by URL -- treat the served root as
  directory-level KEEP unless individual files are provably never requested.

### Blender add-ons

- `__init__.py` with `bl_info` is the platform entry point; Blender imports
  it and calls `register()`. Everything imported from there is reachable.
- Icon/asset loads via `bpy.utils.previews` and datafile paths are edges.
- `blender_manifest.toml` (4.2+ extensions) declares wheels and files.

### Claude Code plugins / skills

- `.claude-plugin/plugin.json` and `marketplace.json` `source` paths.
- Every `SKILL.md` (frontmatter makes it platform-loaded), plus every file
  it links: `references/`, `scripts/`, `assets/`, `agents/`.
- `hooks/hooks.json` commands, `.mcp.json` server entries, `commands/*.md`.
- An unlinked reference document needs a purpose review; executable scripts stay
  protected. A script mentioned in SKILL.md is keep-set even if no code imports it.

This section is for a project that **is** a Claude plugin -- trace it like any
other. Do not confuse it with agent artifacts (`CLAUDE.md`, `.claude/`, plugin
material) left inside an *unrelated* app; active hooks and skills are operational
consumers there too. Review each by role -- see
[agent-artifacts.md](agent-artifacts.md).

### Monorepos

Identify consumers per package/app. A package nothing depends on and no deploy
target ships may warrant separately scoped maintenance; do not archive it as
development residue. Check workspace globs and internal dependencies before
making that recommendation.

## Tracing rules

- **Static edges**: `import`/`require`/`from ... import`, HTML tag
  references, config keys naming files. Follow them transitively.
- **Stylesheets and web assets are edges too**: CSS `url(...)` (fonts,
  background images) and `@import`, `<link rel="icon">`/`manifest` targets,
  `srcset` variants, and everything a `site.webmanifest`/`manifest.json`
  names. An image referenced only from CSS has zero code references and is
  still load-bearing.
- **String-literal paths**: grep the keep-set for quoted paths
  (`open(`, `fetch(`, `readFile(`, `src=`, `href=`). A path built at runtime
  from variables cannot be traced -- see next rule.
- **Dynamic loading widens, never narrows**: glob imports, route
  auto-discovery, plugin registries, template-engine lookups, and
  `import(someVar)` mean the target *directory* joins the keep-set whole.
  Note in the report that precision was lost and why.
- **Config, data, and secrets are implicitly reachable**: dotenv files,
  migration folders, seed data the code opens by convention. When code reads
  a directory rather than a file, keep the directory. The same goes for
  platform-consumed files nothing in the repo references (CI workflows,
  `dependabot.yml`, hosting configs, toolchain dotfiles) -- see
  [evidence-signals.md](evidence-signals.md).
- **Tests are entry points too** (via the test command), which is what makes
  a test for a *deleted* feature detectable: it is reachable from the test
  runner but its subject import is broken or gone -- flag those as
  follow-ups for separately scoped maintenance, not automatic cleanup targets.
- **Ties go to KEEP.** The failure mode of a too-large keep-set is a few
  dead files surviving; the failure mode of a too-small one is a broken
  application. These are not symmetric.
