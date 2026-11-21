# AGENTS.md

Dieses Repo ist eine Spielwiese für einen GenAI-Rahmen mit GitHub Copilot in
VS Code: Skills, Agents, Anweisungen und MCP-Server, zentral im Repository
verwaltet.

- Gespräche und Dokumentation auf Deutsch.
- Geteilte Anpassungen liegen an den Standardorten im Repo und werden
  eingecheckt. Die Übersicht steht in `docs/genai-rahmen.md`.
- Privates gehört nie ins Repo, sondern in das Home-Verzeichnis des Entwicklers.
- Der Nutzer arbeitet in VS Code über Remote-SSH. Nach Änderungen an
  KI-Anpassungen, `.vscode/` oder dieser Datei nennst du kurz, was er in
  VS Code prüfen kann (siehe `README.md`).

## Skills

Prüfe vor jeder Aufgabe, ob ein Skill passt. Lies dafür zuerst den Skill
`using-superpowers`.

Die Superpowers-Skills unter `.agents/skills/` änderst du nicht von Hand.
Sie kommen über ein Skript ins Repo (siehe `tools/superpowers/stand.json`).
