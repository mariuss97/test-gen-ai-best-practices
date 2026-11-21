# Test Gen AI Best Practices

Demo for a shared GenAI framework with GitHub Copilot in VS Code (Remote-SSH,
monorepo). The repo shows where shared and private customizations live. The
guide for the team is in [docs/genai-framework.md](docs/genai-framework.md).

## What is set up

| File | Purpose |
|------|---------|
| `AGENTS.md` | Main instructions for everyone |
| `projects/example-app/AGENTS.md` | Example project with its own rule |
| `.github/instructions/markdown.instructions.md` | Style rules for `**/*.md` |
| `.agents/skills/commit-message/` | Own example skill |
| `.github/agents/reviewer.agent.md` | Agent `reviewer`, may only read and search |
| `.vscode/settings.json` | `chat.useNestedAgentsMdFiles: true` |
| `.vscode/extensions.json` | Recommends GitHub Copilot (`github.copilot-chat`) |
| `.github/skills/` (15 skills and `README.md`) | External skills: copy of Superpowers v7.0.2, kept apart from the own skills in `.agents/skills/` |
| `tools/external-skills/` | Update script, source list `sources.json`, `lock.json`, licenses |
| `.gitignore` | Keeps Claude files out of the repo |
| `docs/genai-framework.md` | Guide for the team |
| `~/.agents/skills/private-example/` | Private skill, lives outside the repo |
| `~/.copilot/mcp-config.json` | Private MCP configuration, lives outside the repo (see the guide) |

## Demo checklist

Prerequisites:

- VS Code is connected to the server over Remote-SSH.
- **This folder** is open as the workspace, not the parent folder `repos`.
- The extension "GitHub Copilot" (ID `github.copilot-chat`) is built into VS
  Code 1.147. Only check that it is active on the SSH side.

Start a **new** chat session after every change.

- [ ] 1. Open the folder over Remote-SSH and mark it as trusted.
- [ ] 2. Open "Chat: Open Customizations":
  - Instructions: `AGENTS.md`, `markdown.instructions.md`
  - Skills: `commit-message` (workspace), `private-example` (personal)
  - Agents: `reviewer`
  - Note: If you have a local `CLAUDE.md`, it also shows up there, because VS
    Code reads it in the built-in mode. This affects only that one machine.
- [ ] 3. Type `/` in the chat: `commit-message` and `private-example` are
  offered.
- [ ] 4. `reviewer` can be selected in the agent picker.
- [ ] 5. Ask the chat about a file in `projects/example-app/`. The references
  show `projects/example-app/AGENTS.md`.
- [ ] 6. No MCP server comes from the repo. Add `azure-devops` to
  `~/.copilot/mcp-config.json` as described in the guide
  ([Private MCP servers](docs/genai-framework.md#private-mcp-servers)). Then
  "MCP: List Servers" shows `azure-devops` with the source "GitHub Copilot
  CLI" (server URL `https://mcp.dev.azure.com/gmhgruppe`). Start the server and sign in with your Microsoft account (Entra ID).
  Then ask in the chat: "List the projects in gmhgruppe." The answer uses a
  tool from `azure-devops` and shows projects. If no connection is made, the
  Linux machine must reach `https://mcp.dev.azure.com` over HTTPS.
- [ ] 7. Extensions, filter "@recommended": GitHub Copilot
  (`github.copilot-chat`) is recommended. VS Code may not show a built-in
  extension there as a recommendation.
- [ ] 8. Superpowers: "Chat: Open Customizations" shows the skills (for
  example `brainstorming`, `writing-plans`) as workspace skills, and
  `/brainstorming` can be called in the chat. In the terminal,
  `python3 tools/external-skills/update.py --check` reports the status.
- [ ] 9. Repeat items 2 to 6 and 8 in both agent modes, as far as the picker
  offers them.
- [ ] 10. Run `git status` in the terminal: the private skill, `CLAUDE.md` and
  `.claude/` do not show up.
