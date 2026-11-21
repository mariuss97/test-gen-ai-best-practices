# Test Gen AI Best Practices

Demo für einen gemeinsamen GenAI-Rahmen mit GitHub Copilot in VS Code
(Remote-SSH, Monorepo). Das Repo zeigt, wo geteilte und private Anpassungen
liegen. Die Anleitung für das Team steht in
[docs/genai-rahmen.md](docs/genai-rahmen.md).

## Was eingerichtet ist

| Datei | Zweck |
|-------|-------|
| `AGENTS.md` | Hauptanweisungen für alle |
| `projekte/beispiel-app/AGENTS.md` | Beispielprojekt mit eigener Regel |
| `.github/instructions/markdown.instructions.md` | Stilregeln für `**/*.md` |
| `.agents/skills/commit-nachricht/` | Eigener Beispiel-Skill |
| `.github/agents/reviewer.agent.md` | Agent `reviewer`, darf nur lesen und suchen |
| `.mcp.json` | Meldet den Azure-DevOps-MCP-Server `azure-devops` an (Remote-Server `https://mcp.dev.azure.com/gmhgruppe`) |
| `.vscode/settings.json` | `chat.useNestedAgentsMdFiles: true` |
| `.vscode/extensions.json` | Empfiehlt GitHub Copilot (`github.copilot-chat`) |
| `.github/skills/` (15 Skills und `README.md`) | Fremde Skills: Kopie von Superpowers v7.0.2, getrennt von den eigenen in `.agents/skills/` |
| `tools/superpowers/` | Update-Skript, `stand.json`, Lizenz |
| `.gitignore` | Hält Claude-Dateien aus dem Repo |
| `docs/genai-rahmen.md` | Anleitung für das Team |
| `~/.agents/skills/privat-beispiel/` | Privater Skill, liegt außerhalb des Repos |

## Prüfliste für die Demo

Voraussetzungen:

- VS Code ist per Remote-SSH mit dem Server verbunden.
- Geöffnet ist **dieser Ordner** als Workspace, nicht der Überordner `repos`.
- Die Erweiterung „GitHub Copilot“ (ID `github.copilot-chat`) ist in VS Code
  1.147 eingebaut. Prüfe nur, dass sie auf der SSH-Seite aktiv ist.

Nach jeder Änderung eine **neue** Chat-Sitzung starten.

- [ ] 1. Den Ordner per Remote-SSH öffnen und als vertrauenswürdig markieren.
- [ ] 2. „Chat: Open Customizations“ öffnen:
  - Instructions: `AGENTS.md`, `markdown.instructions.md`
  - Skills: `commit-nachricht` (Workspace), `privat-beispiel` (persönlich)
  - Agents: `reviewer`
  - Hinweis: Wer lokal eine `CLAUDE.md` hat, sieht sie dort zusätzlich, weil
    VS Code sie im eingebauten Modus liest. Das betrifft nur diesen einen
    Rechner.
- [ ] 3. Im Chat `/` tippen: `commit-nachricht` und `privat-beispiel` werden
  angeboten.
- [ ] 4. In der Agent-Auswahl ist `reviewer` wählbar.
- [ ] 5. Im Chat nach einer Datei in `projekte/beispiel-app/` fragen. In den
  Referenzen erscheint `projekte/beispiel-app/AGENTS.md`.
- [ ] 6. „MCP: List Servers“: `azure-devops` aus `.mcp.json` ist gelistet.
  Server starten und mit dem Microsoft-Konto anmelden (Entra ID). Dann im Chat
  fragen: „Liste die Projekte in gmhgruppe auf.“ Die Antwort nutzt ein
  Werkzeug von `azure-devops` und zeigt Projekte. Kommt keine Verbindung
  zustande, muss der Linux-Rechner `https://mcp.dev.azure.com` per HTTPS
  erreichen.
- [ ] 7. Erweiterungen, Filter „@recommended“: GitHub Copilot
  (`github.copilot-chat`) ist empfohlen. VS Code zeigt eine eingebaute
  Erweiterung dort womöglich nicht als Empfehlung an.
- [ ] 8. Superpowers: „Chat: Open Customizations“ zeigt die Skills (zum
  Beispiel `brainstorming`, `writing-plans`) als Workspace-Skills, und im Chat
  ist `/brainstorming` aufrufbar. Im Terminal meldet
  `python3 tools/superpowers/aktualisieren.py --pruefen` den Stand.
- [ ] 9. Die Punkte 2 bis 6 und 8 in beiden Agent-Modi wiederholen, soweit die
  Auswahl angeboten wird.
- [ ] 10. Im Terminal `git status`: Der private Skill, `CLAUDE.md` und
  `.claude/` tauchen nicht auf.
