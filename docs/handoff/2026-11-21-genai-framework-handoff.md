# Handoff: GenAI framework demo (state of 2026-11-21)

This file lets another agent continue the work at exactly this point. Read it
first, then `AGENTS.md`, `README.md`, `docs/genai-framework.md` and the design
in `docs/superpowers/specs/2026-11-21-genai-framework-design.md`.

## Goal and context

- A software team works in a monorepo with many projects. Everyone uses
  VS Code on Windows and connects over Remote-SSH to a Linux host where the
  repos live. The team uses GitHub Copilot.
- Goal: a shared framework for working with GenAI. Shared customizations
  (instructions, skills, agents, settings) are committed in the repo. Private
  customizations live in each developer's home on the Linux host, never in
  the repo.
- This repo (`test-gen-ai-best-practices`) is the demo. The user opens it in
  VS Code over Remote-SSH, checks that everything is detected, and later
  copies the structure into the real monorepo.
- The solution should be tool-neutral where possible (Copilot today, maybe
  Claude Code or Codex later).

## Where the work stands

- Branch `genai-rahmen` (pushed), 22 commits ahead of `main`.
- Pull request #1, open:
  https://github.com/mariuss97/test-gen-ai-best-practices/pull/1
- Working tree clean. `python3 -m unittest discover -s tests -v` passes
  (57 tests).
- `python3 tools/external-skills/update.py --check` reports
  `superpowers: up to date (v7.0.2)`.

## Structure (what lives where)

| What | Where |
|------|-------|
| Main instructions | `AGENTS.md` |
| Project instructions (example) | `projects/example-app/AGENTS.md` |
| Rules by file pattern | `.github/instructions/markdown.instructions.md` (`**/*.md`), `.github/instructions/java-spring-boot.instructions.md` (`**/*.java`) |
| Own skills | `.agents/skills/` (today `commit-message`) |
| External skills | `.github/skills/` (15 Superpowers skills, v7.0.2, never edit by hand) |
| Update script for external skills | `tools/external-skills/update.py` with `sources.json` (hand-maintained), `lock.json` (script-written), `licenses/<source>/LICENSE` |
| Shared agent | `.github/agents/reviewer.agent.md` (read-only: `read`, `search`) |
| VS Code settings | `.vscode/settings.json` (only `chat.useNestedAgentsMdFiles: true`), `.vscode/extensions.json` (`github.copilot-chat`) |
| MCP | No MCP server in the repo (a test forbids `.mcp.json` and `.vscode/mcp.json`). Private servers go into `~/.copilot/mcp-config.json` |
| Team guide | `docs/genai-framework.md` |
| VS Code checklist | `README.md`, items 1 to 10 |
| Third-party licenses | `docs/third-party-licenses/` |
| Tests | `tests/` (stdlib `unittest`, helpers in `tests/helpers.py`) |

Private demo files on the Linux host (outside the repo):

- `~/.agents/skills/private-example/SKILL.md` (private skill, created by the agent)
- `~/.copilot/agents/private-explainer.agent.md` (private agent, created by the agent)
- `~/.copilot/mcp-config.json` with `azure-devops`
  (`https://mcp.dev.azure.com/gmhgruppe`). The user created this file
  themselves after the agent had removed its test version. Its permissions
  are `664`; the guide recommends `600`. Not changed by the agent.

## Decisions the user made

1. Shared things in the repo, private things in the home on the Linux host
   (not gitignored inside the repo).
2. Keep folder names once chosen. Skills stay in `.agents/skills`, not
   `.claude/skills`.
3. The repo targets GitHub Copilot in VS Code. Do not commit `CLAUDE.md` or
   anything under `.claude/` (both are gitignored; the user keeps local ones).
4. Superpowers is vendored as a copy (not installed as a plugin), so updates
   are deliberate, reviewable diffs.
5. External skills are separated from own skills: external in
   `.github/skills/`, own in `.agents/skills/`.
6. The update script works from a source list, so further sources can be
   added later.
7. No MCP server comes from the repo. The Azure DevOps remote MCP server is
   configured privately. The guide documents this with the `gmhgruppe`
   example.
8. The whole project is in English (file names, code, docs, commit messages).
   The historical plan in `docs/superpowers/plans/` stays German.
9. Spring Boot best practices are based on `github/awesome-copilot` and target
   the team stack: Java 21.0.9, Spring Boot 4.1.1, Gradle 9.7.1 (no Maven).

## What the user verified in VS Code

- The checklist in `README.md` passed (shared instructions, skills, agent,
  nested `AGENTS.md`, Superpowers skills).
- Removing `.mcp.json` made the server disappear without a reload; adding it
  to `~/.copilot/mcp-config.json` made it reappear.
- The private agent in `~/.copilot/agents/` is visible and usable.
- Not yet confirmed by the user: the Spring Boot instructions in a chat (README
  item 5, second part).

## Verified facts (VS Code 1.147.0 source and docs)

- VS Code 1.147.0 runs on the host. Copilot Chat is built in
  (`GitHub.copilot-chat` 0.75.0, shown as "GitHub Copilot").
- Default discovery locations: skills in `.agents/skills`, `.github/skills`,
  `.claude/skills` (one level deep: `<folder>/<skill>/SKILL.md`); agents in
  `.github/agents`, `~/.copilot/agents`; instructions in
  `.github/instructions` (recursive) and `~/.copilot/instructions`.
- `~` resolves to the home on the Linux host in a remote window.
- Standard folders are read directly, so `.gitignore` does not hide files
  there. Nested `AGENTS.md` files are found through workspace search, which
  respects `.gitignore`, `search.exclude` and `files.exclude`.
- Nested `AGENTS.md` in the built-in mode needs
  `chat.useNestedAgentsMdFiles: true`. VS Code then lists them to the model as
  "Instructions for folder '...'" and the model reads them when relevant.
  `.instructions.md` files with `applyTo` are attached automatically when
  matching files are in context.
- `.vscode/settings.json` overrides user and remote settings. There is no
  private counterpart such as `settings.local.json`.
- `~/.copilot/mcp-config.json` is read by default
  (`chat.mcp.discovery.enabled`, source "copilot") and shown with the source
  "GitHub Copilot CLI".
- Plugin folders from the repo would need `chat.pluginLocations`, which is a
  machine-scoped setting and cannot be set in `.vscode/settings.json`.
- Useful method: read the VS Code source at the installed tag with
  `gh api "repos/microsoft/vscode/contents/<path>?ref=1.147.0" -H "Accept: application/vnd.github.raw"`.

Environment notes: Python 3.10 at `/usr/bin/python3`. Node exists only per user
through nvm, so shared tooling must not rely on Node. Network access to
GitHub works.

## Working rules for the next agent

- Write all repository content in English. The user writes German; reply in
  German. (The user's local, gitignored `CLAUDE.md` still says German for
  docs; it is outdated for docs but the user owns it, do not edit it.)
- Never stage or commit `CLAUDE.md` or `.claude/`. Stage files by name, never
  `git add -A` or `git add .`.
- Never edit files in `.github/skills/<skill>/`; change external skills only
  with `tools/external-skills/update.py`.
- Test first, then implement. Keep the suite green and its output clean. A
  test rejects German umlauts in tracked docs and code (except the historical
  plan and vendored skills).
- Commit messages: `<area>: <imperative description>`, a blank line, then
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Push to `genai-rahmen` so changes land in PR #1, and keep the PR
  description in sync.
- After changes to customizations, tell the user what to check in VS Code
  (see `README.md`).

## Open items

1. Ask the user whether the Gradle build uses the Kotlin DSL
   (`build.gradle.kts`) or Groovy, and whether a version catalog
   (`gradle/libs.versions.toml`) exists. Then pin this in
   `.github/instructions/java-spring-boot.instructions.md`.
2. Not yet answered by the user: whether the guide should get the recommended
   pattern for nested instructions (root `AGENTS.md` for everything,
   `AGENTS.md` per project for its specifics, binding rules as
   `.instructions.md` with `applyTo`).
3. The guide could also show the private agent location (`~/.copilot/agents/`)
   with the `private-explainer` example, like the private skill.
4. Known minor gaps (not fixed):
   - `update.py`: invalid data types in `lock.json` give a traceback instead of
     a message; a failed run can leave empty folders; `--check` ignores a
     given version; symlinks in a source are followed.
   - Some helpers (`frontmatter`, `jsonc`) have no dedicated tests.
5. Later: copy the structure into the real monorepo (the guide has a table for
   taking over existing Copilot files) and decide whether to merge PR #1.
