# Design: shared GenAI framework for VS Code and Copilot in a monorepo

Date: 2026-11-21 · Status: approved, updated to the current state (folder names
stay as described).

This document describes the current design. Decisions that changed during the
work are folded into the text. The history of what was considered and why
something was chosen is kept in "Approaches".

## Purpose

A software team works in a monorepo with many projects. Everyone uses VS Code
on Windows and connects over Remote-SSH to a VS Code server on a Linux
machine. The repositories live there too, and each developer has their own
home directory there. Whether each developer has their own clone or several
share one checkout is open. The design works in both cases, because private
files live only in the home directory. The team uses GitHub Copilot. The repo
is designed for Copilot in VS Code, and Claude files are not checked in.

The team wants a uniform framework for development with GenAI:

- Shared customizations (instructions, skills, agents, settings) live in the
  monorepo, are checked in and apply to everyone.
- Everyone can also experiment privately without any of it landing in the repo.
  This includes MCP servers: the repo ships none, and each developer adds them
  privately.
- Today only Copilot is used, but the solution should be as tool-neutral as
  possible, so that other agents (Claude Code, Codex and so on) can be added
  later without a move.
- The Superpowers skills live in the repo as a copy and are available to
  everyone without setup. An update is a deliberate change that is visible in
  the repo.

This repo (`test-gen-ai-best-practices`) is a demo. The user then opens it over
Remote-SSH in VS Code and checks that everything is detected. After that, they
transfer the structure to the real monorepo.

## Goals

- VS Code detects all shared customizations without extra steps, as soon as
  the main folder of the repo is opened over Remote-SSH and marked as trusted.
- Private customizations live in the home directory on the Linux machine and
  are detected as well.
- Where possible, files live in tool-neutral locations that VS Code reads in
  both agent modes (built-in/"Local" and "Copilot") and that other tools read.
- A short guide explains to the team what goes where and contains a checklist.
- The structure can be transferred one to one into the monorepo.

## Non-goals

- No real content for the projects in the monorepo. The demo contains only
  small, easily recognizable examples.
- No organization-wide settings (organization instructions at GitHub,
  enterprise policies).
- No multi-root workspace. The team always opens the main folder of the repo.
- No prompt files (`.prompt.md`). Skills take over this role (they can be
  called as `/name`), and the setting for prompt folders is marked as
  deprecated.
- No Claude files in the repo. `CLAUDE.md` and `.claude/` are not checked in
  but gitignored. The user's local files stay unchanged. Claude Code reads
  skills and agents from `.claude/`, so it does not find the shared skills and
  agents of this structure. That is fine as long as only Copilot is used. The
  guide describes the way for later (see "Guide for the team").
- No MCP server shipped in the repo (see decision 9).

## Anti-goals

The result has failed, even if it works technically, if:

- private files can be checked in by accident,
- the structure works only in the built-in agent mode, which is removed in
  February 2027 according to the docs,
- every developer must first set something up before the **shared**
  customizations take effect,
- the same content has to be maintained in two places (for example in
  `AGENTS.md` and `CLAUDE.md`).

## Constraints (verified)

Verified on 2026-11-21 against the VS Code docs and the source code of VS Code
1.147.0. This version runs on the server, the Copilot extension is
`github.copilot` 1.323.0.

**Standard locations that VS Code searches** (source: `promptFileLocations.ts`):

| Type | In the repo | In the home directory (`~`) |
|------|-------------|-----------------------------|
| Skills | `.agents/skills`, `.github/skills`, `.claude/skills` | `~/.agents/skills`, `~/.copilot/skills`, `~/.claude/skills` |
| Targeted instructions | `.github/instructions` (also subfolders), `.claude/rules` | `~/.copilot/instructions`, `~/.claude/rules` |
| Agents | `.github/agents`, `.claude/agents` | `~/.copilot/agents`, `~/.claude/agents` |
| Hooks | `.github/hooks`, `.claude/settings.json`, `.claude/settings.local.json` | `~/.copilot/hooks`, `~/.claude/settings.json` |
| Project instructions | `AGENTS.md`, `.github/copilot-instructions.md`, `CLAUDE.md` | – |
| MCP servers | `.mcp.json` (main folder), `.vscode/mcp.json` (old) | `~/.copilot/mcp-config.json` (read by VS Code and the Copilot CLI) |

More facts:

- **`~` is the home directory on the Linux machine.** In a remote window, VS
  Code resolves `~` through the remote system (`pathService.userHome()`). So
  private files live per developer on the server, not on Windows.
- **`.gitignore` does not matter for the standard folders.** VS Code reads
  them directly. For this design it is only a side note, because private files
  live outside the repo anyway.
- **Copilot (also the CLI) reads skills from `.agents/skills`**, equal in rank
  to `.github/skills` and `.claude/skills` according to the GitHub docs.
- **`.vscode/settings.json` overrides** the user and remote settings. Order:
  default < user < remote < workspace < policy. Simple values and lists are
  replaced, objects are merged. Some settings apply only globally (for example
  `git.path`, update, security).
- **There is no private counterpart to `.vscode/settings.json`.** Personal
  settings belong in the remote or user settings. They rank **below** the repo:
  whatever is checked in there cannot be overridden privately.
- **`.vscode/extensions.json`** only suggests extensions and installs nothing.
- **`.vscode/launch.json`** adds to the global launch configurations (setting
  `launch`). Both appear side by side (source: `debugConfigurationManager.ts`).
- **MCP files.** `.vscode/mcp.json` is the format of the built-in mode, which
  is removed in February 2027. VS Code 1.147 already reads `.mcp.json` in the
  main folder (format `mcpServers`, source: `workspaceDotMcpDiscovery.ts`), as
  do the Copilot mode and Claude Code. VS Code also reads the private file
  `~/.copilot/mcp-config.json` by default (setting
  `chat.mcp.discovery.enabled`, source "copilot", on by default). It lists
  those servers in "MCP: List Servers" with the source "GitHub Copilot CLI".
  The Copilot CLI reads the same file, and the file can be moved with
  `$COPILOT_HOME`. "MCP: Open Remote User Configuration" offers it as "Copilot
  Remote Configuration (Recommended)". The servers run on the Linux machine.
- **Workspace Trust:** If the folder is not trusted, VS Code blocks agents,
  MCP servers from the repo and parts of the workspace settings.
- **Nested `AGENTS.md`** files in subfolders are read by the Copilot mode on
  its own. The built-in mode needs `chat.useNestedAgentsMdFiles: true` for
  this (experimental, off by default).
- **Agent plugins:** VS Code reads plugin recommendations from
  `.github/copilot/settings.json` and `.github/copilot/settings.local.json`
  (keys `extraKnownMarketplaces` and `enabledPlugins`), and also from
  `.claude/settings.json` (source: `workspacePluginSettingsService.ts`). The
  Copilot CLI also uses the file under `.github/copilot/`.
- VS Code **does not install recommended plugins itself**. It shows "This
  workspace recommends 1 agent plugin." with the button "Show Plugins" (source:
  `claudePluginRecommendations.ts`). Before the first installation, you must
  confirm the marketplace as trusted.
- **Updates:** VS Code checks installed plugins about every 24 hours and
  updates them without asking through `git pull`, as long as
  `extensions.autoUpdate` is on (default). Source: `pluginAutoUpdate.ts` and
  `AGENTS_PLUGINS.md`. On a metered connection the update waits.
- **Superpowers:** The marketplace `obra/superpowers-marketplace` has the
  Claude format (`.claude-plugin/marketplace.json`), which VS Code understands.
  It lists the plugin `superpowers` (7.0.2 today) with the source
  `https://github.com/obra/superpowers.git` and no fixed version. So it always
  points to the latest state. Skills from plugins appear in the chat with the
  plugin name as a prefix, for example `/superpowers:brainstorming`.
- **Plugin from a folder in the repo:** This works only through
  `chat.pluginLocations`. The setting is experimental and has the scope
  "machine" (source: `chat.shared.contribution.ts`). So it must not be in
  `.vscode/settings.json`. Marketplaces that a repo recommends must point to
  GitHub or a Git repo. A folder in the repo itself does not work (source:
  `marketplaceReference.ts`).
- **Superpowers repo:** `https://github.com/obra/superpowers`, MIT license,
  versions as tags (`v7.0.2` = commit `22f0b463e7a5e579904dd6211a520321035526f7`).
  Under `skills/` there are 15 skills. Each is a folder with a `SKILL.md`
  whose header contains only `name` (= folder name) and `description`. Some
  folders contain scripts. There is also a hook (`hooks/session-start`) that
  loads the skill `using-superpowers` at session start.
- Node 22 is available on the server (through nvm), `uvx` is not.
- **Azure DevOps MCP:** Microsoft runs a remote server at
  `https://mcp.dev.azure.com/<organization>` (generally available since August
  2026) and recommends it over the local server (`npx @azure-devops/mcp`).
  Prerequisites: the organization is backed by Microsoft Entra ID, and the
  machine reaches `mcp.dev.azure.com` over HTTPS. Sign-in is through Entra ID,
  and the user's rights in Azure DevOps still apply. It can be restricted with
  the headers `X-MCP-Readonly` and `X-MCP-Toolsets`. Claude Code needs its own
  app registration in Entra ID for it. VS Code 1.147 reads HTTP servers with
  `url` and `headers` (source: `nativeMcpDiscoveryAdapters.ts`).

## Approaches

The core question was where private customizations live.

**A. Private in the same folders in the repo, recognizable by name,
gitignored.** Example: `.agents/skills/local-experiment/`, `test.local.agent.md`.
Advantage: everything is visible in the workspace. Disadvantage: whoever
forgets the naming scheme checks in by accident. Also, an open bug report
([copilot-cli#2544](https://github.com/github/copilot-cli/issues/2544)) says
that the Copilot CLI skips gitignored files. In Copilot mode, private files
might then be invisible.

**B. Private in the home directory on the Linux machine** (`~/.copilot/…`,
`~/.agents/skills`). This is the officially intended place. It applies to all
repos, rules out accidental check-in and works in every mode. Disadvantage:
the files live outside the workspace. You open them through "Chat: Open
Customizations".

**C. A separate gitignored folder in the repo** (for example `.ai-local/`),
registered through settings. Rejected, because the required settings
(`chat.agentSkillsLocations`, `chat.promptFilesLocations`) are marked as
deprecated and only VS Code would know this folder.

**Chosen: B.** The user chose B. Private files may live outside the repo. B is
robust against both modes and the bug report.

For the **shared** files, the options were "everything under `.github/`" and
"tool-neutral where possible". The tool-neutral variant is chosen, because the
user wants it and it costs nothing today: Copilot reads `AGENTS.md` and
`.agents/skills` just like other tools. For agents, targeted instructions and
hooks there is no tool-neutral location, so `.github/` applies there.

For **Superpowers**, these ways were considered:

- **A. Plugin recommendation, VS Code updates itself.** The repo recommends the
  Superpowers marketplace in `.github/copilot/settings.json`, and VS Code keeps
  the installed plugin up to date about daily. Disadvantage: new versions
  arrive unreviewed and not for everyone at the same time, and everyone must
  install the plugin once. Chosen first, then replaced by C1 at the user's
  request.
- **B. Fixed version through a separate marketplace.** A team repo names
  Superpowers with a fixed version. Disadvantage: one more repo.
- **C1. Skills as a copy in `.agents/skills/`.** A script fetches a version and
  replaces the Superpowers folders, and the result is committed. Advantages: no
  setup, both agent modes and the Copilot CLI find the skills, everyone has the
  same version, every update is a reviewable diff. Disadvantages: the skills
  are called `/brainstorming` instead of `/superpowers:brainstorming`, and the
  hook is missing. The replacement for the hook is a hint in `AGENTS.md`.
  Later, the copy moved to `.github/skills/` to keep external skills apart from
  the own ones in `.agents/skills/` (see decision 14).
- **C2. Whole plugin as a copy in `plugins/superpowers/`.** Prefix and hook
  would be kept. Disadvantage: `chat.pluginLocations` must not be in
  `.vscode/settings.json`. Everyone would have to set it themselves, and the
  Copilot CLI does not know the setting.

**Chosen: C1.** The user chose C1. It works for everyone without setup, and
updates stay traceable in the repo.

For **MCP servers**, the options were a shared `.mcp.json` in the repo or a
private file per developer:

- **A. Shared `.mcp.json` with the Azure DevOps remote server.** Everyone gets
  the server without setup. This was the first state of the demo. Disadvantage:
  it presumes that the whole team wants and may use this server.
- **B. Private `~/.copilot/mcp-config.json`.** Each developer decides which
  servers they add. VS Code and the Copilot CLI read the file by default, and
  nothing lands in the repo.

**Chosen: B.** The demo no longer ships `.mcp.json`. The guide documents the
private file with the Azure DevOps example. If the team later wants a shared
server, it goes into `.mcp.json` (format `mcpServers`).

## Decisions

### Shared: in the repo, checked in

| What | Location | Note |
|------|----------|------|
| Main instructions for everyone | `AGENTS.md` in the main folder | The only main file. |
| Instructions for one project | `<project>/AGENTS.md` | Lives next to the project's code. |
| Rules by file pattern | `.github/instructions/<topic>.instructions.md` with `applyTo` | `applyTo` is relative to the main folder of the repo. |
| Skills | `.agents/skills/<name>/SKILL.md` | Folder name = `name` in the frontmatter. |
| Agents | `.github/agents/<name>.agent.md` | |
| Hooks | `.github/hooks/` | Documented only, no demo. |
| MCP servers | None shipped; `.mcp.json` in the main folder if the team decides | Format `mcpServers`. Enter no secrets. Only servers whose runtime is available system-wide on the server for everyone. |
| Editor settings | `.vscode/settings.json` | Only what must be the same for everyone. |
| Recommended extensions | `.vscode/extensions.json` | |
| External skills (Superpowers) | `.github/skills/<name>/` as a copy, kept apart from the own skills, status in `tools/external-skills/lock.json` | Never edit by hand, only through `tools/external-skills/update.py`. |
| Debug configurations | `.vscode/launch.json` | Unchanged as before, not part of the demo. |

### Private: in the home directory on the Linux machine

| What | Location |
|------|----------|
| Personal standing instructions | `~/.copilot/instructions/<name>.instructions.md` with `applyTo: "**"` |
| Personal rules by file pattern | `~/.copilot/instructions/<topic>.instructions.md` |
| Skills | `~/.agents/skills/<name>/SKILL.md` |
| Agents | `~/.copilot/agents/<name>.agent.md` |
| Hooks | `~/.copilot/hooks/` |
| MCP servers | `~/.copilot/mcp-config.json` (or `$COPILOT_HOME/mcp-config.json`), format `mcpServers`; the guide has the Azure DevOps example |
| VS Code settings | Remote settings ("Preferences: Open Remote Settings") |
| Plugins to try out | Install them in VS Code through the plugin view. This applies only to you, no file in the repo is needed. |

A private skill that has the same name as a shared one should be avoided. The
guide recommends the prefix `private-` for private skills.

### `.gitignore`

Private AI files do not live in the repo. For Claude Code, the guide recommends
`~/.claude/CLAUDE.md` and `~/.claude/settings.json`. These entries keep Claude
files out of the repo:

- `CLAUDE.md`
- `CLAUDE.local.md`
- `.claude/` (also covers the former line `.claude/settings.local.json`, which
  is therefore dropped)

The Python cache `__pycache__/` and `.superpowers/` (session data of the skill
`brainstorming`) are ignored as well. A comment in `.gitignore` points out that
private customizations belong in the home directory.

### Demo in this repo

| File | Purpose | How to check that it is detected |
|------|---------|----------------------------------|
| `AGENTS.md` | Contains the purpose of the repo, the language rule (repository content in English, replies in the user's language), the hint about the check in VS Code, and a pointer to the guide. Replaces the Superpowers hook with the hint to check before each task whether a skill fits, and to read the skill `using-superpowers` for that. Also explains that `superpowers:<name>` means the skill `<name>` under `.github/skills/`. | Appears under "Instructions"; is named as a reference in answers. |
| `projects/example-app/AGENTS.md` and `README.md` | Example project with its own, easily recognizable rule (answers start with "Rules from projects/example-app/AGENTS.md active."). | Question about a file in the project: the answer names this `AGENTS.md` as a reference. |
| `.github/instructions/markdown.instructions.md` | Style rules for docs (English, short sentences, sentence-case headings, tables for comparisons), `applyTo: "**/*.md"`. | Appears under "Instructions"; applies when editing `.md` files. |
| `.github/instructions/java-spring-boot.instructions.md` | Spring Boot backend best practices, `applyTo: "**/*.java"`. Adapted from `instructions/springboot.instructions.md` in `github/awesome-copilot` (MIT, commit 942a83b0a080) and extended (web layer with DTOs and `ProblemDetail`, transactions, persistence, testing). License in `docs/third-party-licenses/awesome-copilot-LICENSE`. | Creating a `.java` file in chat shows it in the references. |
| `.agents/skills/commit-message/SKILL.md` | Writes a commit message from the changes. Example format: `<area>: <imperative description>`, blank line, bullet points. Marked in the skill as an example that the team replaces with its real format. Only suggests the message, never commits. | Appears under "Skills" as a workspace skill and as `/commit-message`. |
| `.github/agents/reviewer.agent.md` | Reviews changes, may only read and search, changes nothing (`tools: ['read', 'search']`). | Appears in the agent picker as "reviewer". |
| `.vscode/settings.json` | `chat.useNestedAgentsMdFiles: true`, with a comment why. Nothing else. | The setting is set in the workspace tab. |
| `.vscode/extensions.json` | Recommends the Copilot extension. | Under extensions "@recommended". |
| `tools/external-skills/update.py` | Reads the source list, fetches a version of a source with `git clone` (default: latest tag `v*`) and replaces only the folders listed in `lock.json`. Aborts without changes if a new skill has the same name as an own folder or a skill from another source, or if fetching fails. `--check` reports whether a newer version exists. Standard library and `git` only. | `python3 tools/external-skills/update.py --check` reports "up to date". |
| `tools/external-skills/sources.json` | List of external sources, Superpowers is the first entry. Keys: `url`, `path`, `license`, `only`, `exclude`. | |
| `tools/external-skills/lock.json` (written by the script) | Source, version, commit, list of the copied skill folders, per source. | Shows `v7.0.2`. |
| `tools/external-skills/licenses/<source>/LICENSE` (copied by the script) | MIT license of Superpowers, required for copies. | |
| `.github/skills/<15 Superpowers skills>/` (copied by the script) and `.github/skills/README.md` | The skills of Superpowers `v7.0.2`, unchanged. | Appear under "Skills" as workspace skills; `/brainstorming` can be called. |
| `.gitignore` | See above. | |
| `docs/genai-framework.md` | Guide for the team, kept general, see below. | |
| `README.md` | Short: what is set up, link to the guide, and the checklist for the demo files (see below). | |
| `~/.agents/skills/private-example/SKILL.md` (**outside the repo**, in the user's home directory on this machine) | Shows that private skills are detected. | Appears under "Skills" as a personal skill; `git status` shows nothing. |
| `~/.copilot/mcp-config.json` (**outside the repo**, optional) | Private MCP configuration with the Azure DevOps remote server: name `azure-devops`, `type: http`, URL `https://mcp.dev.azure.com/gmhgruppe`. No runtime on the server needed, sign-in through Microsoft Entra ID. | "MCP: List Servers" shows `azure-devops` with the source "GitHub Copilot CLI". After sign-in, a question about the projects of `gmhgruppe` returns results. |

`CLAUDE.md` and `.claude/settings.json` stay local with the user, unchanged and
gitignored. The current `CLAUDE.md` still says `.claude/` is checked in. The
user adapts that themselves if needed.

### Guide for the team (`docs/genai-framework.md`)

Short and meant to be copied into the monorepo. The structure and this guide
move into the monorepo. The demo files are only examples. So the guide is
worded generally and names the demo files at most as an example. Content:

1. **What goes where:** the two tables "Shared" and "Private" from above.
2. **Rules:**
   - Put only what must be the same for everyone in `.vscode/settings.json`,
     because nobody can override it privately.
   - No secrets in `.mcp.json` or other checked-in files.
   - Shared MCP servers preferably remote over HTTP; local ones only with
     runtimes that are installed system-wide on the server (not per user, for
     example through nvm).
   - Private skills with the prefix `private-`.
   - Always put private things in the home directory, also for Claude Code
     (`~/.claude/`).
   - Never edit external skills (today Superpowers) by hand, only through
     their update script. Put your own changes in your own skills.
   - Agree on new external sources with the team first, because skills can
     bring scripts that run on the server.
   - Try new shared customizations privately first, then move them into the
     repo.
3. **Create private folders once:** one `mkdir -p` command for the private
   folders.
4. **Private MCP servers:** the file `~/.copilot/mcp-config.json`, how VS Code
   and the Copilot CLI read it, the Azure DevOps example, `chmod 600`,
   prerequisites, optional headers, and where a shared server would go.
5. **Check that everything is detected:** general procedure through "Chat: Open
   Customizations", "MCP: List Servers" and the references of a chat answer.
   The concrete checklist for the demo is in the README.
6. **Take over existing files in the monorepo:**

   | Existing | What to do |
   |----------|------------|
   | `.github/copilot-instructions.md` | Move the content into `AGENTS.md`, delete the file. Otherwise both load and the content is duplicated. |
   | `.github/prompts/*.prompt.md` | Convert to skills under `.agents/skills/`. |
   | `.github/chatmodes/*.chatmode.md` | Move to `.github/agents/` as `.agent.md`. |
   | `.github/skills/` with own skills | Move to `.agents/skills/`. `.github/skills/` is reserved for external skills. |
   | `.vscode/mcp.json` | Move the servers by hand to `~/.copilot/mcp-config.json` or, if shared, to `.mcp.json` (`servers` becomes `mcpServers`), delete the file. |
   | AI settings in `.vscode/settings.json` | Check whether they should apply to everyone. Move personal ones to the remote settings. |

7. **Adding Claude Code later:** The folder names stay as they are for now. The
   guide contains this transfer table:

   | Part | For Claude Code | Effort |
   |------|-----------------|--------|
   | `AGENTS.md` in the main folder | `CLAUDE.md` with `@AGENTS.md`, then remove it from `.gitignore` | none |
   | Superpowers copy in `.github/skills/` | moves with the other skills to `.claude/skills/` (adjust the target folder in the script), or Claude Code installs the plugin itself | small |
   | `.mcp.json` (if the team shares servers) | Claude Code reads it directly; the Azure DevOps remote server needs its own app registration in Entra ID | small |
   | Skills in `.agents/skills/` | same format, but Claude Code searches only in `.claude/skills/` | move the folders (do not link them, otherwise VS Code shows every skill twice) |
   | `AGENTS.md` per project | one `CLAUDE.md` with `@AGENTS.md` per project | small |
   | Rules in `.github/instructions/` | to `.claude/rules/`, `applyTo` becomes `paths` in the frontmatter | mechanical |
   | Agents in `.github/agents/` | to `.claude/agents/`, different tool names in the frontmatter | rewrite each agent |
   | Hooks in `.github/hooks/` | different format in `.claude/settings.json` | rewrite |
   | Private files in `~/.copilot/…`, `~/.agents/skills/` | `~/.claude/…` | move |

8. **Updating external skills:**
   - Check: `python3 tools/external-skills/update.py --check`
   - Update: `python3 tools/external-skills/update.py` (latest version) or
     with a version, for example `… superpowers v7.0.3`
   - Then look at `git diff --stat`, read the Superpowers release notes,
     commit and hand it to the team through a pull request.
   - Going back to an older version works the same way, with its tag.
   - New sources go into `sources.json`; the guide describes the keys and how
     to resolve a skill name that exists in two sources (`exclude`).

### Checklist for the demo (in the README)

1. Open the main folder of the repo over Remote-SSH and mark it as trusted.
2. Open "Chat: Open Customizations":
   - Instructions: `AGENTS.md`, `markdown.instructions.md`, `java-spring-boot.instructions.md`
   - Skills: `commit-message` (workspace), `private-example` (personal)
   - Agents: `reviewer`
3. Type `/` in the chat: `commit-message` and `private-example` are offered.
4. Agent picker: `reviewer` can be selected.
5. Ask the chat about a file in `projects/example-app/`: the references show
   `projects/example-app/AGENTS.md`.
6. No MCP server comes from the repo. Add `azure-devops` to
   `~/.copilot/mcp-config.json` as in the guide. "MCP: List Servers" shows
   `azure-devops` with the source "GitHub Copilot CLI". Start it, sign in with
   the Microsoft account and ask in the chat: "List the projects in
   gmhgruppe."
7. Extensions, filter "@recommended": Copilot is recommended.
8. Superpowers: "Chat: Open Customizations" shows the Superpowers skills (for
   example `brainstorming`, `writing-plans`) as workspace skills, and
   `/brainstorming` can be called in the chat. In the terminal,
   `python3 tools/external-skills/update.py --check` reports the status.
9. Repeat items 2 to 6 and 8 in both agent modes, as far as the picker offers
   them.
10. Run `git status` in the terminal: the private skill, `CLAUDE.md` and
    `.claude/` do not show up.

## Left to the implementer

- Exact wording of the example content. It must be short and clearly
  recognizable by one feature.
- Valid tool names in the frontmatter of `reviewer.agent.md`. Resolved:
  `read` and `search`, the built-in tool sets in VS Code 1.147.
- The exact ID of the Copilot extension for `extensions.json`. Resolved:
  `github.copilot-chat`, built into VS Code 1.147 and shown as "GitHub Copilot".
- Whether VS Code offers a built-in transfer from `.vscode/mcp.json` to
  `.mcp.json`. It does not in 1.147, so the guide describes the manual move.

## My decisions (please review)

I set these points; they were not explicitly discussed:

1. `AGENTS.md` is the only main file. `CLAUDE.md` and `.claude/` do not go
   into the repo (user decision), but into `.gitignore`.
2. Own skills live in `.agents/skills` instead of `.github/skills`.
3. No MCP server is shipped in the repo. Each developer adds MCP servers in
   the private `~/.copilot/mcp-config.json`. A shared `.mcp.json` is an option
   the team can decide on later.
4. No prompt files, skills instead.
5. Project instructions as `AGENTS.md` in the project folder, plus the
   experimental setting for the built-in mode.
6. Hooks are only documented, not demonstrated.
7. A private example skill is created in your home directory on this machine.
8. The guide lives in `docs/genai-framework.md`. It is general, and the
   checklist for the demo is in the README.
9. The Azure DevOps remote MCP server (user decision, organization
   `gmhgruppe`) is documented as the example in the private MCP
   configuration, not shipped as `.mcp.json`. My choices: remote instead of
   local through `npx`, because Node is installed here only per user through
   nvm and Microsoft recommends the remote server; all tools enabled, no
   `X-MCP-Readonly`.
10. The commit format in the example skill is a placeholder that you replace
    with your real format.
11. Claude Code does not find the shared skills and agents for now. This is
    intended as long as you only use Copilot.
12. Private things always live in the home directory, also for Claude Code. The
    entries in `.gitignore` are only a safety net.
13. The guide contains a table on how to take over existing Copilot files in
    the monorepo.
14. Superpowers lives as a copy in `.github/skills/`, kept apart from the own
    skills in `.agents/skills/` (way C1, separation at the user's request). My
    choices: all 15 skills are copied, nothing is left out. The script is
    written in Python and fetches the files through `git`. The status lives in
    `tools/external-skills/`, not in the skill folder. The license is copied
    along. `AGENTS.md` replaces the hook. The script reads a source list
    (`tools/external-skills/sources.json`), Superpowers is the first entry. The
    status of all sources is in a `lock.json`, the licenses are under
    `tools/external-skills/licenses/<source>/`. The same skill name in two
    sources is resolved with `exclude`.
15. The README has no section about Claude Code anymore.
16. All repository content is written in English. Replies follow the language
    the user writes in. The original execution plan
    (`docs/superpowers/plans/2026-11-21-genai-rahmen.md`) stays in German as a
    historical record.
