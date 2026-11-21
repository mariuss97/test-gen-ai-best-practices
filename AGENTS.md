# AGENTS.md

This repo is a playground for a GenAI framework with GitHub Copilot in
VS Code: skills, agents, instructions and MCP servers, managed centrally in
the repository.

- Write all repository content (docs, code, comments, commit messages) in
  English. Reply in the language the user writes in.
- Shared customizations live in the standard locations in the repo and are
  checked in. The overview is in `docs/genai-framework.md`.
- Private things never go into the repo. They belong in the developer's home
  directory.
- The user works in VS Code over Remote-SSH. After changes to AI
  customizations, `.vscode/` or this file, briefly tell them what they can
  check in VS Code (see `README.md`).

## Skills

Before each task, check whether a skill fits. To do so, first read the skill
`using-superpowers`.

Own skills live in `.agents/skills/`, external skills in `.github/skills/`.
Do not edit the external skills (today Superpowers) under `.github/skills/` by
hand. They come into the repo through a script (see
`tools/external-skills/lock.json`).
`superpowers:<name>` in the Superpowers skills means the skill `<name>` under
`.github/skills/`.
