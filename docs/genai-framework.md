# GenAI framework for VS Code and Copilot

This guide describes where shared and private AI customizations live. It
applies to VS Code 1.147 with Remote-SSH and GitHub Copilot. Always open the
main folder of the repo and mark it as trusted. Otherwise VS Code blocks
agents, MCP servers from the repo and parts of the workspace settings.

The locations are tool-neutral where possible. Today the team uses only
Copilot. Other agents can be added later (see below).

## What goes where

Shared means: in the repo, checked in, applies to everyone.

| What | Location | Note |
|------|----------|------|
| Main instructions for everyone | `AGENTS.md` in the main folder | The only main file |
| Instructions for one project | `<project>/AGENTS.md` | Lives next to the project's code |
| Rules by file pattern | `.github/instructions/<topic>.instructions.md` with `applyTo` | `applyTo` is relative to the main folder |
| Skills | `.agents/skills/<name>/SKILL.md` | Folder name = `name` in the frontmatter |
| Agents | `.github/agents/<name>.agent.md` | |
| Hooks | `.github/hooks/` | |
| MCP servers | None shipped; `.mcp.json` in the main folder if the team decides | Format `mcpServers` |
| Editor settings | `.vscode/settings.json` | Only what must be the same for everyone |
| Recommended extensions | `.vscode/extensions.json` | Only suggests, installs nothing |
| External skills (Superpowers) | `.github/skills/<name>/` as a copy, kept apart from the own skills in `.agents/skills/` | Status in `tools/external-skills/lock.json` |

Private means: in the home directory on the Linux machine. In a remote window,
VS Code resolves `~` on the server. So private files live per developer on the
server, not on Windows and never in the repo.

| What | Location |
|------|----------|
| Personal standing instructions | `~/.copilot/instructions/<name>.instructions.md` with `applyTo: "**"` |
| Personal rules by file pattern | `~/.copilot/instructions/<topic>.instructions.md` |
| Skills | `~/.agents/skills/<name>/SKILL.md` |
| Agents | `~/.copilot/agents/<name>.agent.md` |
| Hooks | `~/.copilot/hooks/` |
| MCP servers | `~/.copilot/mcp-config.json` (see "Private MCP servers") |
| VS Code settings | Remote settings: "Preferences: Open Remote Settings" (file `~/.vscode-server/data/Machine/settings.json`) |
| Plugins to try out | Install them in the VS Code plugin view. They apply only to you |

Settings precedence: default, user, remote, workspace, policy. So the
workspace (`.vscode/settings.json`) beats user and remote. Simple values and
lists are replaced, objects are merged. Some settings apply only globally, for
example `git.path`. There is no private counterpart to `.vscode/settings.json`.

## Rules

- Put only what must be the same for everyone in `.vscode/settings.json`.
  Nobody can override it privately.
- No secrets in `.mcp.json` or other checked-in files.
- Shared MCP servers should preferably be remote servers over HTTP, like Azure
  DevOps (`https://mcp.dev.azure.com/<organization>`). Use local servers only
  with runtimes that are installed system-wide on the server, not per user (for
  example through nvm).
- Private skills get the prefix `private-`. This way they do not collide with
  shared skills.
- Always put private things in the home directory, also for Claude Code
  (`~/.claude/`).
- Never edit external skills (today Superpowers) by hand, only through their
  update script. Put your own changes in your own skills.
- Agree on new external sources with the team first (procedure: see "Updating
  external skills"). Skills can bring scripts that run on the server.
- Try new shared customizations privately first, then move them into the repo.

Superpowers lives in the repo as a copy and not as a plugin. This needs no
setup, everyone has the same version, and every update is a reviewable diff.
The skills are then called `/brainstorming` instead of
`/superpowers:brainstorming`.

With the copy, the plugin's hook that loads `using-superpowers` at session
start is missing. The repo's `AGENTS.md` therefore needs this hint, ready to
copy:

```markdown
Before each task, check whether a skill fits. To do so, first read the skill
`using-superpowers`.
```

`superpowers:<name>` in the Superpowers skills means the skill `<name>` under
`.github/skills/`. It is best to add this sentence to `AGENTS.md` as well.

## Create private folders

Once, on the Linux machine:

```bash
mkdir -p ~/.copilot/instructions ~/.copilot/agents ~/.copilot/hooks ~/.agents/skills
```

## Private MCP servers

The repo ships no MCP server. Each developer adds MCP servers privately on the
Linux host in `~/.copilot/mcp-config.json` (or `$COPILOT_HOME/mcp-config.json`).

- VS Code reads this file by default (setting `chat.mcp.discovery.enabled`,
  source "copilot", on by default). It lists the servers in "MCP: List
  Servers" with the source "GitHub Copilot CLI".
- The Copilot CLI reads the same file.
- "MCP: Open Remote User Configuration" offers it as "Copilot Remote
  Configuration (Recommended)".

Example with the remote Azure DevOps server:

```json
{
  "mcpServers": {
    "azure-devops": {
      "type": "http",
      "url": "https://mcp.dev.azure.com/gmhgruppe"
    }
  }
}
```

Run `chmod 600 ~/.copilot/mcp-config.json`. The file needs no secrets: you
sign in through Microsoft Entra ID when the server starts.

Prerequisites for the Azure DevOps remote server:

- The organization is backed by Microsoft Entra ID.
- The host reaches `https://mcp.dev.azure.com` over HTTPS. "Connection
  refused" usually means a firewall or proxy.

Optionally restrict the server with headers, for example
`"headers": {"X-MCP-Readonly": "true"}` or
`"headers": {"X-MCP-Toolsets": "repos,wiki,wit"}`.

If the team later wants a shared server, it goes into `.mcp.json` at the repo
root (format `mcpServers`). The rule above still applies: shared servers
preferably remote over HTTP, local ones only with a system-wide runtime.

## Check that everything is detected

Start a new chat session after changes.

| What to check | How |
|---------------|-----|
| Instructions, skills, agents | "Chat: Open Customizations". Shared ones appear as workspace, private ones as personal |
| Skills as commands | Type `/` in the chat |
| Agents | In the agent picker |
| Instructions in use | The references of a chat answer show the file that was used |
| MCP servers | "MCP: List Servers": private servers show the source "GitHub Copilot CLI", status running |
| Recommended extensions | Extensions, filter "@recommended" |
| Nothing private in the repo | `git status` |

The concrete checklist for the demo files is in the README of the demo repo
`test-gen-ai-best-practices`.

## Take over existing files in the monorepo

| Existing | What to do |
|----------|------------|
| `.github/copilot-instructions.md` | Move the content into `AGENTS.md`, delete the file. Otherwise both load and the content is duplicated |
| `.github/prompts/*.prompt.md` | Convert to skills under `.agents/skills/` |
| `.github/chatmodes/*.chatmode.md` | Move to `.github/agents/` as `.agent.md` |
| `.github/skills/` with own skills | Move to `.agents/skills/`. `.github/skills/` is reserved for external skills |
| `.vscode/mcp.json` | Move the servers by hand to the private `~/.copilot/mcp-config.json` (`servers` becomes `mcpServers`), or to `.mcp.json` if the team decides to share them, then delete the old file. VS Code 1.147 offers no command for this |
| AI settings in `.vscode/settings.json` | Check whether they should apply to everyone. Move personal ones to the remote settings |

## Adding Claude Code later

Claude Code reads skills and agents from `.claude/`. So for now it does not
find the shared skills and agents of this structure. The folder names stay as
they are. For later, this transfer applies:

| Part | For Claude Code | Effort |
|------|-----------------|--------|
| `AGENTS.md` in the main folder | `CLAUDE.md` with `@AGENTS.md`, then remove it from `.gitignore` | none |
| Superpowers copy in `.github/skills/` | Moves with the other skills to `.claude/skills/` (adjust the target folder in the script). Or Claude Code installs the plugin itself | small |
| `.mcp.json` (if the team shares servers) | Claude Code reads it directly. The Azure DevOps remote server needs its own app registration in Entra ID there | small |
| Skills in `.agents/skills/` | Same format, but Claude Code searches only in `.claude/skills/`. Move the folders, do not link them, otherwise VS Code shows every skill twice | small |
| `AGENTS.md` per project | One `CLAUDE.md` with `@AGENTS.md` per project | small |
| Rules in `.github/instructions/` | To `.claude/rules/`, `applyTo` becomes `paths` in the frontmatter | mechanical |
| Agents in `.github/agents/` | To `.claude/agents/`, different tool names in the frontmatter | rewrite each agent |
| Hooks in `.github/hooks/` | Different format in `.claude/settings.json` | rewrite |
| Private files in `~/.copilot/…`, `~/.agents/skills/` | To `~/.claude/…` | move |

After that, skills, rules and agents live under `.claude/`, and `CLAUDE.md` is
checked in. Both are in the `.gitignore` today, and `git add` then refuses
them. Remove `.claude/` and `CLAUDE.md` from the `.gitignore` and keep only
`.claude/settings.local.json` and `CLAUDE.local.md` ignored.

Private Claude files belong in `~/.claude/CLAUDE.md` and
`~/.claude/settings.json`. These lines belong in the `.gitignore`: `CLAUDE.md`,
`CLAUDE.local.md`, `.claude/` and `.superpowers/` (the skill `brainstorming`
stores session data there). If the repo has Python tests, add `__pycache__/`.

## Updating external skills

The sources are listed in `tools/external-skills/sources.json`, Superpowers is
the first entry. The status of each source is in
`tools/external-skills/lock.json`, the licenses are under
`tools/external-skills/licenses/<source>/`.

| Step | Command or action |
|------|-------------------|
| Check all sources | `python3 tools/external-skills/update.py --check` |
| Check one source | `python3 tools/external-skills/update.py --check superpowers` |
| Update all sources to the latest version | `python3 tools/external-skills/update.py` |
| Update one source to the latest version | `python3 tools/external-skills/update.py superpowers` |
| Update one source to a fixed version | `python3 tools/external-skills/update.py superpowers v7.0.3` |
| Review the changes | `git status` (new folders) and `git diff --stat` |
| Read the release notes | [Superpowers on GitHub](https://github.com/obra/superpowers) |
| Hand it to the team | Commit and open a pull request |

Going back to an older version works the same way, with its tag. The script
aborts without changes if fetching fails or if a new skill has the same name as
an own folder or as a skill from another source.

### Adding a new source

1. Agree on the source with the team and check the license. It must allow
   copying.
2. Add an entry to `tools/external-skills/sources.json`. The source name
   consists of lowercase letters, digits and hyphens.
3. Run `python3 tools/external-skills/update.py <name>`.
4. Use `git status` to check which folders are new. New skills are not tracked
   yet and therefore missing from `git diff`. So first run
   `git add .github/skills tools/external-skills`, then use
   `git diff --cached --stat` to see what comes into the repo.
5. Commit and open a pull request.

Each source has these keys:

| Key | Meaning | Default |
|-----|---------|---------|
| `url` | Git URL of the source (required) | |
| `path` | Folder in the source with `<skill>/SKILL.md` | `skills` |
| `license` | License file in the source | `LICENSE` |
| `only` | List: take only these skills | all |
| `exclude` | List: do not take these skills | none |

`only` and `exclude` cannot be combined. Typos in either list show up, because
the script looks up every name in the source.

### Same skill name in two sources

If a skill has the same name in two sources, the script aborts and names both
sources. Leave the skill out for one source with `exclude`, for example
`"exclude": ["brainstorming"]`, and run the script again.

### Private repos

Private repos, for example in Azure DevOps, use the normal Git credentials on
the machine. The script only calls `git`. If `git clone <url>` works there, the
script works too. Never put credentials into `sources.json`.
