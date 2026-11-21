# GenAI-Rahmen für VS Code und Copilot

Diese Anleitung beschreibt, wo geteilte und private KI-Anpassungen liegen. Sie
gilt für VS Code 1.147 mit Remote-SSH und GitHub Copilot. Immer den Hauptordner
des Repos öffnen und als vertrauenswürdig markieren. Sonst sperrt VS Code
Agents, MCP-Server aus dem Repo und Teile der Workspace-Einstellungen.

Die Orte sind werkzeugneutral gewählt, wo es geht. Heute nutzt das Team nur
Copilot, andere Agenten lassen sich später ergänzen (siehe unten).

## Was liegt wo

Geteilt heißt: im Repo, eingecheckt, gilt für alle.

| Was | Ort | Hinweis |
|-----|-----|---------|
| Hauptanweisungen für alle | `AGENTS.md` im Hauptordner | Einzige Hauptdatei |
| Anweisungen für ein Projekt | `<projekt>/AGENTS.md` | Liegt beim Code des Projekts |
| Regeln nach Dateimuster | `.github/instructions/<thema>.instructions.md` mit `applyTo` | `applyTo` bezieht sich auf den Hauptordner |
| Skills | `.agents/skills/<name>/SKILL.md` | Ordnername = `name` im Frontmatter |
| Agents | `.github/agents/<name>.agent.md` | |
| Hooks | `.github/hooks/` | |
| MCP-Server | `.mcp.json` im Hauptordner | Format `mcpServers` |
| Editor-Einstellungen | `.vscode/settings.json` | Nur, was für alle gleich sein muss |
| Empfohlene Erweiterungen | `.vscode/extensions.json` | Schlägt nur vor, installiert nichts |
| Fremde Skills (Superpowers) | `.agents/skills/<name>/` als Kopie | Stand in `tools/superpowers/stand.json` |

Privat heißt: im Home-Verzeichnis auf dem Linux-Rechner. VS Code löst `~` in
einem Remote-Fenster auf dem Server auf. Private Dateien liegen also pro
Entwickler auf dem Server, nicht auf Windows und nie im Repo.

| Was | Ort |
|-----|-----|
| Persönliche Daueranweisungen | `~/.copilot/instructions/<name>.instructions.md` mit `applyTo: "**"` |
| Persönliche Regeln nach Dateimuster | `~/.copilot/instructions/<thema>.instructions.md` |
| Skills | `~/.agents/skills/<name>/SKILL.md` |
| Agents | `~/.copilot/agents/<name>.agent.md` |
| Hooks | `~/.copilot/hooks/` |
| MCP-Server | Copilot-Modus: `~/.copilot/mcp-config.json`. Eingebauter Modus: „MCP: Open Remote User Configuration“ |
| VS-Code-Einstellungen | Remote-Einstellungen: „Preferences: Open Remote Settings“ (Datei `~/.vscode-server/data/Machine/settings.json`) |
| Plugins zum Ausprobieren | In der Plugin-Ansicht von VS Code installieren. Gilt nur für einen selbst |

Rangfolge der Einstellungen: Standard, User, Remote, Workspace, Richtlinie. Der
Workspace (`.vscode/settings.json`) schlägt also User und Remote. Einfache
Werte und Listen werden ersetzt, Objekte zusammengeführt. Einige Einstellungen
gelten nur global, zum Beispiel `git.path`. Es gibt kein privates Gegenstück zu
`.vscode/settings.json`.

## Regeln

- In `.vscode/settings.json` nur, was für alle gleich sein muss. Niemand kann
  es privat übersteuern.
- Keine Geheimnisse in `.mcp.json` oder anderen eingecheckten Dateien.
- Geteilte MCP-Server nur mit Laufzeiten, die auf dem Server systemweit
  installiert sind, nicht pro Nutzer (zum Beispiel über nvm).
- Private Skills bekommen den Präfix `privat-`. So kollidieren sie nicht mit
  geteilten Skills.
- Privates immer ins Home, auch für Claude Code (`~/.claude/`).
- Fremde Skills (heute Superpowers) nie von Hand ändern, nur über ihr
  Update-Skript. Eigene Anpassungen gehören in eigene Skills.
- Neue Fremdquellen vorher im Team abstimmen. Skills können Skripte
  mitbringen, die auf dem Server laufen.
- Neue geteilte Anpassungen zuerst privat ausprobieren, dann ins Repo
  verschieben.

Superpowers liegt als Kopie im Repo und nicht als Plugin. Das braucht keine
Einrichtung, alle haben dieselbe Version, und jedes Update ist ein prüfbarer
Diff. Die Skills heißen dann `/brainstorming` statt `/superpowers:brainstorming`.

Bei der Kopie entfällt der Hook des Plugins, der `using-superpowers` zu
Sitzungsbeginn lädt. Die `AGENTS.md` des Repos braucht deshalb diesen Hinweis,
zum Kopieren:

```markdown
Prüfe vor jeder Aufgabe, ob ein Skill passt. Lies dafür zuerst den Skill
`using-superpowers`.
```

`superpowers:<name>` in den Superpowers-Skills meint den Skill `<name>` unter `.agents/skills/`. Diesen Satz nimmst du am besten ebenfalls in die `AGENTS.md` auf.

## Private Ordner anlegen

Einmalig auf dem Linux-Rechner:

```bash
mkdir -p ~/.copilot/instructions ~/.copilot/agents ~/.copilot/hooks ~/.agents/skills
```

## Prüfen, ob alles erkannt wird

Nach Änderungen eine neue Chat-Sitzung starten.

| Was prüfen | Wie |
|------------|-----|
| Anweisungen, Skills, Agents | „Chat: Open Customizations“. Geteilte erscheinen als Workspace, private als persönlich |
| Skills als Befehl | Im Chat `/` tippen |
| Agents | In der Agent-Auswahl |
| Anweisungen im Einsatz | In den Referenzen einer Chat-Antwort steht die genutzte Datei |
| MCP-Server | „MCP: List Servers“: Quelle `.mcp.json`, Status läuft |
| Empfohlene Erweiterungen | Erweiterungen, Filter „@recommended“ |
| Nichts Privates im Repo | `git status` |

Im Repo `test-gen-ai-best-practices` steht die konkrete Prüfliste für die
Demo-Dateien im README des Demo-Repos.

## Bestehendes im Monorepo übernehmen

| Vorhanden | Was tun |
|-----------|---------|
| `.github/copilot-instructions.md` | Inhalt in `AGENTS.md` übernehmen, Datei löschen. Sonst laden beide, und Inhalte doppeln sich |
| `.github/prompts/*.prompt.md` | In Skills unter `.agents/skills/` umwandeln |
| `.github/chatmodes/*.chatmode.md` | Als `.agent.md` nach `.github/agents/` verschieben |
| `.github/skills/` | Nach `.agents/skills/` verschieben |
| `.vscode/mcp.json` | Von Hand nach `.mcp.json` übertragen (`servers` wird zu `mcpServers`), dann die alte Datei löschen. VS Code 1.147 bietet dafür keinen Befehl |
| KI-Einstellungen in `.vscode/settings.json` | Prüfen, ob sie für alle gelten sollen. Persönliches in die Remote-Einstellungen verschieben |

## Später Claude Code dazunehmen

Claude Code liest Skills und Agents aus `.claude/`. Die geteilten Skills und
Agents dieser Struktur findet es deshalb vorerst nicht. Die Ordnernamen bleiben,
wie sie sind. Für später gilt diese Übertragung:

| Teil | Für Claude Code | Aufwand |
|------|-----------------|---------|
| `AGENTS.md` im Hauptordner | `CLAUDE.md` mit `@AGENTS.md`, dann aus `.gitignore` nehmen | keiner |
| Superpowers-Kopie in `.agents/skills/` | Zieht mit den anderen Skills nach `.claude/skills/` um (Zielordner im Skript anpassen). Oder Claude Code installiert das Plugin selbst | klein |
| `.mcp.json` | Liest Claude Code direkt | keiner |
| Skills in `.agents/skills/` | Gleiches Format, aber Claude Code sucht nur in `.claude/skills/`. Ordner verschieben, nicht verlinken, sonst zeigt VS Code jeden Skill doppelt | klein |
| `AGENTS.md` pro Projekt | Je Projekt eine `CLAUDE.md` mit `@AGENTS.md` | klein |
| Regeln in `.github/instructions/` | Nach `.claude/rules/`, im Frontmatter wird `applyTo` zu `paths` | mechanisch |
| Agents in `.github/agents/` | Nach `.claude/agents/`, andere Werkzeugnamen im Frontmatter | jeden Agent umschreiben |
| Hooks in `.github/hooks/` | Anderes Format in `.claude/settings.json` | neu schreiben |
| Privates in `~/.copilot/…`, `~/.agents/skills/` | Nach `~/.claude/…` | verschieben |

Skills, Regeln und Agents liegen danach unter `.claude/`, und `CLAUDE.md` wird eingecheckt. Beides steht heute in der `.gitignore`, `git add` verweigert sie dann. Nimm `.claude/` und `CLAUDE.md` aus der `.gitignore` und lass nur `.claude/settings.local.json` und `CLAUDE.local.md` ignoriert.

Private Claude-Dateien gehören nach `~/.claude/CLAUDE.md` und
`~/.claude/settings.json`. Diese Zeilen gehören in die `.gitignore`: `CLAUDE.md`,
`CLAUDE.local.md`, `.claude/` und `.superpowers/` (der Skill `brainstorming`
legt dort Sitzungsdaten an). Hat das Repo Python-Tests, kommt `__pycache__/` dazu.

## Superpowers aktualisieren

| Schritt | Befehl oder Aktion |
|---------|--------------------|
| Prüfen, ob es eine neuere Version gibt | `python3 tools/superpowers/aktualisieren.py --pruefen` |
| Aktualisieren auf die neueste Version | `python3 tools/superpowers/aktualisieren.py` |
| Aktualisieren auf eine feste Version | `python3 tools/superpowers/aktualisieren.py v7.0.3` |
| Änderungen ansehen | `git diff --stat` |
| Release-Notes lesen | [Superpowers auf GitHub](https://github.com/obra/superpowers) |
| Ins Team geben | Committen und Pull Request öffnen |

Zurück auf eine ältere Version geht genauso, mit deren Tag. Das Skript bricht
ohne Änderung ab, wenn das Holen scheitert oder ein neuer Skill wie ein eigener
Ordner heißt.
