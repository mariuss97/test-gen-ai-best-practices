# Test Gen AI Best Practices

Spielwiese, um Best Practices für Claude Code auszuprobieren: Skills, Agents,
Plugins, Hooks und Einstellungen, die zentral in diesem Repository verwaltet
werden.

## Was eingerichtet ist

| Datei | Zweck |
|-------|-------|
| `.claude/settings.json` | Aktiviert das Plugin [Superpowers](https://github.com/obra/superpowers) aus dem offiziellen Marketplace `claude-plugins-official`, nur für dieses Repo |
| `CLAUDE.md` | Projektkontext, den Claude bei jedem Start liest |
| `.gitignore` | Hält persönliche Einstellungen (`.claude/settings.local.json`) aus dem Repo |

Designs aus dem Brainstorming legt Superpowers unter `docs/superpowers/specs/` ab.

## Prüfen, ob VS Code alles erkennt

Voraussetzungen:

- VS Code ist per Remote-SSH mit dem Server verbunden.
- Geöffnet ist **dieser Ordner** als Workspace, nicht der Überordner `repos`.
  Projekteinstellungen gelten nur, wenn Claude im Repo startet.
- Die Erweiterung „Claude Code“ ist auf der SSH-Seite installiert.

Nach jeder Änderung an `.claude/` oder `CLAUDE.md` eine **neue** Claude-Sitzung
starten, weil Plugins, Skills und `CLAUDE.md` beim Start geladen werden.

| Prüfung | Erwartung |
|---------|-----------|
| Im Claude-Panel `/super` tippen | `superpowers:brainstorming` und weitere Superpowers-Skills werden vorgeschlagen |
| Claude fragen: „Was weißt du über dieses Repo?“ | Antwort nimmt Bezug auf `CLAUDE.md` (Spielwiese für Best Practices, Deutsch) |
| Im integrierten Terminal: `claude plugin list` | `superpowers@claude-plugins-official`, Scope `project`, Status `enabled` |
| Gegenprobe im Überordner `repos`: `claude plugin list` | Superpowers ist dort `disabled` |
