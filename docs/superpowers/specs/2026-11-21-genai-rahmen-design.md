# Design: Gemeinsamer GenAI-Rahmen für VS Code und Copilot im Monorepo

Stand: 2026-11-21 · Status: freigegeben (Ordnernamen bleiben wie beschrieben).
Nachträge am selben Tag, ebenfalls freigegeben: Claude-Dateien kommen nicht ins
Repo. Die Skills von Superpowers liegen als Kopie im Repo und werden per Skript
aktualisiert. Diese Kopie ersetzt die zwischenzeitlich geplante
Plugin-Empfehlung. Außerdem ersetzt der Remote-MCP-Server von Azure DevOps
(Organisation `gmhgruppe`) den Demo-MCP-Server. Fremde Skills liegen getrennt
von den eigenen in `.github/skills/` (eigene weiter in `.agents/skills/`).

## Absicht

Ein Softwareteam arbeitet in einem Monorepo mit vielen Projekten. Alle nutzen
VS Code auf Windows und verbinden sich per Remote-SSH mit einem VS-Code-Server
auf einem Linux-Rechner. Dort liegen auch die Repositories, und jeder
Entwickler hat dort ein eigenes Home-Verzeichnis. Ob jeder einen eigenen Clone
hat oder ob sich mehrere einen Checkout teilen, ist offen. Der Entwurf
funktioniert in beiden Fällen, weil Privates nur im Home liegt. Das Team nutzt
GitHub Copilot. Das Repo ist für Copilot in VS Code ausgelegt, und
Claude-Dateien werden nicht eingecheckt.

Das Team möchte einen einheitlichen Rahmen für die Entwicklung mit GenAI:

- Geteilte Anpassungen (Anweisungen, Skills, Agents, MCP-Server, Einstellungen)
  liegen im Monorepo, werden eingecheckt und gelten für alle.
- Jeder kann außerdem privat experimentieren, ohne dass etwas davon im Repo
  landet.
- Heute wird nur Copilot genutzt, die Lösung soll aber möglichst
  werkzeugneutral sein, damit später andere Agenten (Claude Code, Codex usw.)
  ohne Umzug dazukommen können.
- Die Skills von Superpowers liegen als Kopie im Repo und stehen allen ohne
  Einrichtung zur Verfügung. Ein Update ist eine bewusste, im Repo sichtbare
  Änderung.

Dieses Repo (`test-gen-ai-best-practices`) dient als Demo. Der Nutzer öffnet es
anschließend per Remote-SSH in VS Code und prüft, ob alles erkannt wird. Danach
überträgt er die Struktur in das echte Monorepo.

## Ziele

- VS Code erkennt alle geteilten Anpassungen ohne Zusatzschritte, sobald der
  Hauptordner des Repos per Remote-SSH geöffnet und als vertrauenswürdig
  markiert ist.
- Private Anpassungen liegen im Home-Verzeichnis auf dem Linux-Rechner und
  werden ebenfalls erkannt.
- Wo es geht, liegen Dateien an werkzeugneutralen Orten, die VS Code in beiden
  Agent-Modi (eingebaut/„Local“ und „Copilot“) und weitere Werkzeuge lesen.
- Eine kurze Anleitung erklärt dem Team, was wo hingehört, und enthält eine
  Prüfliste.
- Die Struktur lässt sich eins zu eins ins Monorepo übertragen.

## Nicht-Ziele

- Keine echten Inhalte für die Projekte im Monorepo. Die Demo enthält nur
  kleine, gut erkennbare Beispiele.
- Keine organisationsweiten Einstellungen (Organisations-Anweisungen bei
  GitHub, Enterprise-Richtlinien).
- Kein Multi-Root-Workspace. Das Team öffnet immer den Hauptordner des Repos.
- Keine Prompt-Dateien (`.prompt.md`). Skills übernehmen diese Rolle (sie
  lassen sich als `/name` aufrufen), und die Einstellung für Prompt-Ordner ist
  als veraltet markiert.
- Keine Claude-Dateien im Repo. `CLAUDE.md` und `.claude/` werden nicht
  eingecheckt, sondern gitignored. Lokale Dateien des Nutzers bleiben
  unverändert liegen. Claude Code liest Skills und Agents aus `.claude/`,
  findet die geteilten Skills und Agents dieser Struktur also nicht. Das ist in
  Ordnung, solange nur Copilot genutzt wird. Die Anleitung nennt den Weg für
  später (siehe „Anleitung“).

## Anti-Ziele

Das Ergebnis ist gescheitert, auch wenn es technisch läuft, wenn:

- private Dateien versehentlich eingecheckt werden können,
- die Struktur nur im eingebauten Agent-Modus funktioniert, der laut Doku im
  Februar 2027 entfällt,
- jeder Entwickler erst etwas einrichten muss, damit die **geteilten**
  Anpassungen wirken,
- derselbe Inhalt an zwei Stellen gepflegt werden muss (z. B. in `AGENTS.md`
  und `CLAUDE.md`).

## Rahmenbedingungen (geprüft)

Geprüft am 2026-11-21 gegen die VS-Code-Doku und den Quellcode von VS Code
1.147.0. Diese Version läuft auf dem Server, die Copilot-Erweiterung ist
`github.copilot` 1.323.0.

**Standardorte, die VS Code durchsucht** (Quelle: `promptFileLocations.ts`):

| Typ | Im Repo | Im Home (`~`) |
|-----|---------|---------------|
| Skills | `.agents/skills`, `.github/skills`, `.claude/skills` | `~/.agents/skills`, `~/.copilot/skills`, `~/.claude/skills` |
| Gezielte Anweisungen | `.github/instructions` (auch Unterordner), `.claude/rules` | `~/.copilot/instructions`, `~/.claude/rules` |
| Agents | `.github/agents`, `.claude/agents` | `~/.copilot/agents`, `~/.claude/agents` |
| Hooks | `.github/hooks`, `.claude/settings.json`, `.claude/settings.local.json` | `~/.copilot/hooks`, `~/.claude/settings.json` |
| Projektanweisungen | `AGENTS.md`, `.github/copilot-instructions.md`, `CLAUDE.md` | – |
| MCP-Server | `.mcp.json` (Hauptordner), `.vscode/mcp.json` (alt) | `~/.copilot/mcp-config.json` (Copilot-Modus) |

Weitere Fakten:

- **`~` ist das Home auf dem Linux-Rechner.** In einem Remote-Fenster löst VS
  Code `~` über das Remote-System auf (`pathService.userHome()`). Private
  Dateien liegen also pro Entwickler auf dem Server, nicht auf Windows.
- **`.gitignore` spielt für die Standardordner keine Rolle.** VS Code liest
  sie direkt ein. Für diesen Entwurf ist das nur eine Randnotiz, weil private
  Dateien ohnehin außerhalb des Repos liegen.
- **Copilot (auch die CLI) liest Skills aus `.agents/skills`**, laut GitHub-Doku
  gleichrangig zu `.github/skills` und `.claude/skills`.
- **`.vscode/settings.json` überschreibt** die User- und Remote-Einstellungen.
  Reihenfolge: Standard < User < Remote < Workspace < Richtlinie. Einfache
  Werte und Listen werden ersetzt, Objekte zusammengeführt. Einige
  Einstellungen gelten nur global (z. B. `git.path`, Update, Sicherheit).
- **Es gibt kein privates Gegenstück zu `.vscode/settings.json`.** Persönliche
  Einstellungen gehören in die Remote- oder User-Einstellungen. Die haben
  Vorrang **unter** dem Repo: Was dort eingecheckt ist, kann niemand privat
  übersteuern.
- **`.vscode/extensions.json`** schlägt Erweiterungen nur vor und installiert
  nichts.
- **`.vscode/launch.json`** ergänzt die globalen Startkonfigurationen (Einstellung
  `launch`). Beide erscheinen nebeneinander (Quelle: `debugConfigurationManager.ts`).
- **`.vscode/mcp.json`** ist das Format des eingebauten Modus, der im Februar
  2027 entfällt. **`.mcp.json` im Hauptordner** (Format `mcpServers`) liest VS
  Code 1.147 bereits (Quelle: `workspaceDotMcpDiscovery.ts`), ebenso der
  Copilot-Modus und Claude Code. Die Server laufen auf dem Linux-Rechner.
- **Workspace Trust:** Ist der Ordner nicht vertrauenswürdig, sperrt VS Code
  Agents, MCP-Server aus dem Repo und Teile der Workspace-Einstellungen.
- **Verschachtelte `AGENTS.md`** in Unterordnern liest der Copilot-Modus von
  selbst. Der eingebaute Modus braucht dafür `chat.useNestedAgentsMdFiles: true`
  (experimentell, Standard aus).
- **Agent Plugins:** VS Code liest Plugin-Empfehlungen aus
  `.github/copilot/settings.json` und `.github/copilot/settings.local.json`
  (Schlüssel `extraKnownMarketplaces` und `enabledPlugins`), außerdem aus
  `.claude/settings.json` (Quelle: `workspacePluginSettingsService.ts`). Die
  Datei unter `.github/copilot/` nutzt auch die Copilot-CLI.
- VS Code **installiert empfohlene Plugins nicht selbst**. Es zeigt „This
  workspace recommends 1 agent plugin.“ mit dem Knopf „Show Plugins“ (Quelle:
  `claudePluginRecommendations.ts`). Vor der ersten Installation muss man den
  Marktplatz als vertrauenswürdig bestätigen.
- **Aktualisierung:** VS Code prüft installierte Plugins etwa alle 24 Stunden
  und aktualisiert sie ohne Nachfrage per `git pull`, solange
  `extensions.autoUpdate` an ist (Standard). Quelle: `pluginAutoUpdate.ts` und
  `AGENTS_PLUGINS.md`. Bei getakteter Verbindung wartet die Aktualisierung.
- **Superpowers:** Der Marktplatz `obra/superpowers-marketplace` hat das
  Claude-Format (`.claude-plugin/marketplace.json`), das VS Code versteht. Er
  nennt das Plugin `superpowers` (heute 7.0.2) mit der Quelle
  `https://github.com/obra/superpowers.git` ohne feste Version. Er zeigt also
  immer auf den neuesten Stand. Skills aus Plugins erscheinen im Chat mit dem
  Plugin-Namen als Präfix, z. B. `/superpowers:brainstorming`.
- **Plugin aus einem Ordner im Repo:** Das geht nur über `chat.pluginLocations`.
  Die Einstellung ist experimentell und hat den Gültigkeitsbereich „machine“
  (Quelle: `chat.shared.contribution.ts`). Sie darf also nicht in
  `.vscode/settings.json` stehen. Marktplätze, die ein Repo empfiehlt, müssen
  auf GitHub oder ein Git-Repo zeigen. Ein Ordner im Repo selbst geht nicht
  (Quelle: `marketplaceReference.ts`).
- **Superpowers-Repo:** `https://github.com/obra/superpowers`, Lizenz MIT,
  Versionen als Tags (`v7.0.2` = Commit `22f0b463e7a5e579904dd6211a520321035526f7`).
  Unter `skills/` liegen 15 Skills. Jeder ist ein Ordner mit `SKILL.md`, der
  Dateikopf enthält nur `name` (= Ordnername) und `description`. Einige
  Ordner enthalten Skripte. Dazu kommt ein Hook (`hooks/session-start`), der
  beim Sitzungsstart den Skill `using-superpowers` lädt.
- Auf dem Server ist Node 22 vorhanden (über nvm), `uvx` nicht.
- **Azure DevOps MCP:** Microsoft betreibt einen Remote-Server unter
  `https://mcp.dev.azure.com/<organisation>` (allgemein verfügbar seit August
  2026) und empfiehlt ihn vor dem lokalen Server (`npx @azure-devops/mcp`).
  Voraussetzungen: Die Organisation hängt an Microsoft Entra ID, der Rechner
  erreicht `mcp.dev.azure.com` per HTTPS. Anmeldung per Entra ID, die Rechte
  des Nutzers in Azure DevOps gelten weiter. Einschränken lässt er sich über
  die Header `X-MCP-Readonly` und `X-MCP-Toolsets`. Claude Code braucht dafür
  eine eigene App-Registrierung in Entra ID. VS Code 1.147 liest HTTP-Server
  mit `url` und `headers` aus `.mcp.json` (Quelle: `nativeMcpDiscoveryAdapters.ts`).

## Ansätze

Die Kernfrage war, wo private Anpassungen liegen.

**A. Privat in denselben Ordnern im Repo, am Namen erkennbar, gitignored.**
Beispiel: `.agents/skills/local-experiment/`, `test.local.agent.md`. Vorteil:
Alles liegt sichtbar im Workspace. Nachteil: Wer das Namensschema vergisst,
checkt aus Versehen ein. Außerdem meldet ein offener Fehlerbericht
([copilot-cli#2544](https://github.com/github/copilot-cli/issues/2544)), dass
die Copilot-CLI gitignorte Dateien auslässt. Im Copilot-Modus wären private
Dateien dann womöglich unsichtbar.

**B. Privat im Home-Verzeichnis auf dem Linux-Rechner** (`~/.copilot/…`,
`~/.agents/skills`). Das ist der offiziell vorgesehene Ort. Er gilt für alle
Repos, schließt versehentliches Einchecken aus und wirkt in jedem Modus.
Nachteil: Die Dateien liegen außerhalb des Workspace. Man öffnet sie über
„Chat: Open Customizations“.

**C. Eigener gitignorter Ordner im Repo** (z. B. `.ai-local/`), über
Einstellungen angemeldet. Verworfen, weil die nötigen Einstellungen
(`chat.agentSkillsLocations`, `chat.promptFilesLocations`) als veraltet markiert
sind und nur VS Code diesen Ordner kennen würde.

**Gewählt: B.** Der Nutzer hat B gewählt. Private Dateien dürfen außerhalb des
Repos liegen. B ist robust gegenüber beiden Modi und dem Fehlerbericht.

Für die **geteilten** Dateien wurde zwischen „alles unter `.github/`“ und
„werkzeugneutral, wo möglich“ abgewogen. Gewählt ist die werkzeugneutrale
Variante, weil der Nutzer sie sich wünscht und sie heute nichts kostet:
`AGENTS.md`, `.agents/skills` und `.mcp.json` liest Copilot genauso wie andere
Werkzeuge. Für Agents, gezielte Anweisungen und Hooks gibt es keinen
werkzeugneutralen Ort, dort gilt `.github/`.

Für **Superpowers** wurden diese Wege abgewogen:

- **A. Plugin-Empfehlung, VS Code aktualisiert selbst.** Das Repo empfiehlt
  den Superpowers-Marktplatz in `.github/copilot/settings.json`, und VS Code
  hält das installierte Plugin etwa täglich aktuell. Nachteil: Neue Versionen
  kommen ungeprüft und nicht bei allen gleichzeitig an, und jeder muss das
  Plugin einmal installieren. Zuerst gewählt, dann vom Nutzer durch C1
  ersetzt.
- **B. Feste Version über einen eigenen Marktplatz.** Ein Team-Repo nennt
  Superpowers mit fester Version. Nachteil: ein zusätzliches Repo.
- **C1. Skills als Kopie in `.agents/skills/`.** Ein Skript holt eine Version
  und ersetzt die Superpowers-Ordner, das Ergebnis wird committet. Vorteile:
  keine Einrichtung, beide Agent-Modi und die Copilot-CLI finden die Skills,
  alle haben dieselbe Version, jedes Update ist ein prüfbarer Diff. Nachteile:
  Die Skills heißen `/brainstorming` statt `/superpowers:brainstorming`, und
  der Hook entfällt. Ersatz für den Hook ist ein Hinweis in `AGENTS.md`.
- **C2. Ganzes Plugin als Kopie in `plugins/superpowers/`.** Präfix und Hook
  blieben erhalten. Nachteil: `chat.pluginLocations` darf nicht in
  `.vscode/settings.json` stehen. Jeder müsste es selbst setzen, und die
  Copilot-CLI kennt die Einstellung nicht.

**Gewählt: C1.** Der Nutzer hat C1 gewählt. Es funktioniert bei jedem ohne
Einrichtung, und Updates bleiben im Repo nachvollziehbar.

## Entscheidungen

### Geteilt: im Repo, eingecheckt

| Was | Ort | Hinweis |
|-----|-----|---------|
| Hauptanweisungen für alle | `AGENTS.md` im Hauptordner | Einzige Hauptdatei. |
| Anweisungen für ein Projekt | `<projekt>/AGENTS.md` | Liegt beim Code des Projekts. |
| Regeln nach Dateimuster | `.github/instructions/<thema>.instructions.md` mit `applyTo` | `applyTo` bezieht sich auf den Hauptordner des Repos. |
| Skills | `.agents/skills/<name>/SKILL.md` | Ordnername = `name` im Frontmatter. |
| Agents | `.github/agents/<name>.agent.md` | |
| Hooks | `.github/hooks/` | Nur dokumentiert, keine Demo. |
| MCP-Server | `.mcp.json` im Hauptordner | Format `mcpServers`. Keine Geheimnisse eintragen. Nur Server, deren Laufzeit für alle auf dem Server systemweit verfügbar ist. |
| Editor-Einstellungen | `.vscode/settings.json` | Nur, was für alle gleich sein muss. |
| Empfohlene Erweiterungen | `.vscode/extensions.json` | |
| Fremde Skills (Superpowers) | `.github/skills/<name>/` als Kopie, getrennt von den eigenen Skills, Stand in `tools/superpowers/stand.json` | Nie von Hand ändern, nur über `tools/superpowers/aktualisieren.py`. |
| Debug-Konfigurationen | `.vscode/launch.json` | Unverändert wie bisher, nicht Teil der Demo. |

### Privat: im Home auf dem Linux-Rechner

| Was | Ort |
|-----|-----|
| Persönliche Daueranweisungen | `~/.copilot/instructions/<name>.instructions.md` mit `applyTo: "**"` |
| Persönliche Regeln nach Dateimuster | `~/.copilot/instructions/<thema>.instructions.md` |
| Skills | `~/.agents/skills/<name>/SKILL.md` |
| Agents | `~/.copilot/agents/<name>.agent.md` |
| Hooks | `~/.copilot/hooks/` |
| MCP-Server | Copilot-Modus: `~/.copilot/mcp-config.json`; eingebauter Modus: „MCP: Open Remote User Configuration“ |
| VS-Code-Einstellungen | Remote-Einstellungen („Preferences: Open Remote Settings“) |
| Plugins zum Ausprobieren | In VS Code über die Plugin-Ansicht installieren. Das gilt nur für einen selbst, eine Datei im Repo ist nicht nötig. |

Ein privater Skill, der denselben Namen hat wie ein geteilter, ist zu
vermeiden. Die Anleitung empfiehlt dafür den Präfix `privat-` für private
Skills.

### `.gitignore`

Private KI-Dateien liegen nicht im Repo. Für Claude Code empfiehlt die
Anleitung `~/.claude/CLAUDE.md` und `~/.claude/settings.json`. Diese Einträge
halten Claude-Dateien aus dem Repo:

- `CLAUDE.md`
- `CLAUDE.local.md`
- `.claude/` (deckt auch die bisherige Zeile `.claude/settings.local.json` ab,
  die deshalb entfällt)

Ein Kommentar in `.gitignore` verweist darauf, dass private Anpassungen ins Home
gehören.

### Demo in diesem Repo

| Datei | Zweck | Woran man das Erkennen prüft |
|-------|-------|------------------------------|
| `AGENTS.md` (neu) | Übernimmt den Inhalt der heutigen `CLAUDE.md` (Zweck des Repos, Deutsch, Hinweis zur VS-Code-Prüfung) und verweist auf die Anleitung. Ersetzt den Superpowers-Hook mit dem Hinweis, vor jeder Aufgabe zu prüfen, ob ein Skill passt, und dafür den Skill `using-superpowers` zu lesen. | Erscheint unter „Instructions“; wird in Antworten als Referenz genannt. |
| `projekte/beispiel-app/AGENTS.md` und `README.md` (neu) | Beispielprojekt mit einer eigenen, gut erkennbaren Regel. | Frage zu einer Datei im Projekt: Die Antwort nennt diese `AGENTS.md` als Referenz. |
| `.github/instructions/markdown.instructions.md` (neu) | Stilregeln für Doku, `applyTo: "**/*.md"`. | Erscheint unter „Instructions“; greift beim Bearbeiten von `.md`-Dateien. |
| `.agents/skills/commit-nachricht/SKILL.md` (neu) | Schreibt eine Commit-Nachricht aus den Änderungen. Beispielformat: `<bereich>: <Beschreibung im Imperativ>`, Leerzeile, Stichpunkte. Im Skill als Beispiel gekennzeichnet, das das Team durch sein echtes Format ersetzt. | Erscheint unter „Skills“ als Workspace-Skill und als `/commit-nachricht`. |
| `.github/agents/reviewer.agent.md` (neu) | Prüft Änderungen, darf nur lesen und suchen, nichts ändern. | Erscheint in der Agent-Auswahl als „reviewer“. |
| `.mcp.json` (neu) | Meldet den Remote-MCP-Server von Azure DevOps an: Name `azure-devops`, `type: http`, URL `https://mcp.dev.azure.com/gmhgruppe`. Keine Laufzeit auf dem Server nötig, Anmeldung per Microsoft Entra ID in VS Code. | „MCP: List Servers“ zeigt `azure-devops`. Nach der Anmeldung liefert eine Frage nach den Projekten von `gmhgruppe` Ergebnisse. |
| `.vscode/settings.json` (neu) | `chat.useNestedAgentsMdFiles: true`, mit Kommentar warum. Sonst nichts. | Einstellung ist im Workspace-Tab gesetzt. |
| `.vscode/extensions.json` (neu) | Empfiehlt die Copilot-Erweiterung. | Unter Erweiterungen „@recommended“. |
| `tools/superpowers/aktualisieren.py` (neu) | Holt eine Superpowers-Version per `git clone` (Standard: neuester Tag `v*`) und ersetzt nur die Ordner, die in `stand.json` stehen. Bricht ohne Änderung ab, wenn ein neuer Skill wie ein eigener Ordner heißt oder das Holen scheitert. `--pruefen` meldet, ob es eine neuere Version gibt. Nur Standardbibliothek und `git`. | `python3 tools/superpowers/aktualisieren.py --pruefen` meldet „aktuell“. |
| `tools/superpowers/stand.json` (neu, vom Skript geschrieben) | Quelle, Version, Commit, Liste der kopierten Skill-Ordner. | Steht auf `v7.0.2`. |
| `tools/superpowers/LICENSE` (neu, vom Skript kopiert) | MIT-Lizenz von Superpowers, Pflicht bei Kopien. | |
| `.github/skills/<15 Superpowers-Skills>/` (neu, vom Skript kopiert) und `.github/skills/README.md` | Die Skills von Superpowers `v7.0.2`, unverändert. | Erscheinen unter „Skills“ als Workspace-Skills; `/brainstorming` ist aufrufbar. |
| `.gitignore` (geändert) | Siehe oben. | |
| `docs/genai-rahmen.md` (neu) | Anleitung für das Team, allgemein gehalten, siehe unten. | |
| `README.md` (geändert) | Kurz: was eingerichtet ist, Link zur Anleitung, und die Prüfliste für die Demo-Dateien (siehe unten). | |
| `~/.agents/skills/privat-beispiel/SKILL.md` (neu, **außerhalb des Repos**, im Home des Nutzers auf diesem Rechner) | Zeigt, dass private Skills erkannt werden. | Erscheint unter „Skills“ als persönlicher Skill; `git status` zeigt nichts. |

`CLAUDE.md` und `.claude/settings.json` bleiben lokal beim Nutzer liegen,
unverändert und gitignored. Die heutige `CLAUDE.md` sagt noch, `.claude/` werde
eingecheckt. Das passt der Nutzer bei Bedarf selbst an.

### Anleitung für das Team (`docs/genai-rahmen.md`)

Kurz und zum Kopieren ins Monorepo gedacht. Ins Monorepo wandern die Struktur
und diese Anleitung. Die Demo-Dateien sind nur Beispiele. Deshalb ist die
Anleitung allgemein formuliert und nennt die Demo-Dateien höchstens als
Beispiel. Inhalt:

1. **Was liegt wo:** die beiden Tabellen „Geteilt“ und „Privat“ von oben.
2. **Regeln:**
   - In `.vscode/settings.json` nur, was für alle gleich sein muss, weil es
     niemand privat übersteuern kann.
   - Keine Geheimnisse in `.mcp.json` oder anderen eingecheckten Dateien.
   - Geteilte MCP-Server nur mit Laufzeiten, die systemweit auf dem Server
     installiert sind (nicht pro Nutzer, z. B. über nvm).
   - Private Skills mit Präfix `privat-`.
   - Privates immer ins Home, auch für Claude Code (`~/.claude/`).
   - Fremde Skills (heute Superpowers) nie von Hand ändern, nur über ihr
     Update-Skript. Eigene Anpassungen gehören in eigene Skills.
   - Neue Fremdquellen vorher im Team abstimmen, denn Skills können Skripte
     mitbringen, die auf dem Server laufen.
   - Neue geteilte Anpassungen erst privat ausprobieren, dann ins Repo
     verschieben.
3. **Private Ordner einmalig anlegen:** ein `mkdir -p`-Befehl für die privaten
   Ordner.
4. **Prüfen, ob alles erkannt wird:** allgemeines Vorgehen über „Chat: Open
   Customizations“, „MCP: List Servers“ und die Referenzen einer Chat-Antwort.
   Die konkrete Prüfliste für die Demo steht im README.
5. **Bestehendes im Monorepo übernehmen:**

   | Vorhanden | Was tun |
   |-----------|---------|
   | `.github/copilot-instructions.md` | Inhalt in `AGENTS.md` übernehmen, Datei löschen. Sonst laden beide, und Inhalte doppeln sich. |
   | `.github/prompts/*.prompt.md` | In Skills unter `.agents/skills/` umwandeln. |
   | `.github/chatmodes/*.chatmode.md` | Als `.agent.md` nach `.github/agents/` verschieben. |
   | `.github/skills/` mit eigenen Skills | Nach `.agents/skills/` verschieben. `.github/skills/` ist für fremde Skills reserviert. |
   | `.vscode/mcp.json` | Server nach `.mcp.json` übertragen (`servers` wird zu `mcpServers`), Datei löschen. |
   | KI-Einstellungen in `.vscode/settings.json` | Prüfen, ob sie für alle gelten sollen. Persönliches in die Remote-Einstellungen verschieben. |

6. **Später Claude Code dazunehmen:** Die Ordnernamen bleiben vorerst, wie sie
   sind. Die Anleitung enthält diese Übertragungstabelle:

   | Teil | Für Claude Code | Aufwand |
   |------|-----------------|---------|
   | `AGENTS.md` im Hauptordner | `CLAUDE.md` mit `@AGENTS.md`, dann aus `.gitignore` nehmen | keiner |
   | Superpowers-Kopie in `.github/skills/` | zieht mit den anderen Skills nach `.claude/skills/` um (Zielordner im Skript anpassen), oder Claude Code installiert das Plugin selbst | klein |
   | `.mcp.json` | liest Claude Code direkt | keiner |
   | Skills in `.agents/skills/` | gleiches Format, Claude Code sucht aber nur in `.claude/skills/` | Ordner verschieben (nicht verlinken, sonst zeigt VS Code jeden Skill doppelt) |
   | `AGENTS.md` pro Projekt | je Projekt eine `CLAUDE.md` mit `@AGENTS.md` | klein |
   | Regeln in `.github/instructions/` | nach `.claude/rules/`, im Frontmatter wird `applyTo` zu `paths` | mechanisch |
   | Agents in `.github/agents/` | nach `.claude/agents/`, andere Werkzeugnamen im Frontmatter | jeden Agent umschreiben |
   | Hooks in `.github/hooks/` | anderes Format in `.claude/settings.json` | neu schreiben |
   | Privates in `~/.copilot/…`, `~/.agents/skills/` | `~/.claude/…` | verschieben |

7. **Superpowers aktualisieren:**
   - Prüfen: `python3 tools/superpowers/aktualisieren.py --pruefen`
   - Aktualisieren: `python3 tools/superpowers/aktualisieren.py` (neueste
     Version) oder mit Versionsangabe, z. B. `… v7.0.3`
   - Danach `git diff --stat` ansehen, die Release-Notes von Superpowers lesen,
     committen und per Pull Request ins Team geben.
   - Zurück auf eine ältere Version geht genauso, mit deren Tag.

### Prüfliste für die Demo (im README)

1. Repo-Hauptordner per Remote-SSH öffnen und als vertrauenswürdig markieren.
2. „Chat: Open Customizations“ öffnen:
   - Instructions: `AGENTS.md`, `markdown.instructions.md`
   - Skills: `commit-nachricht` (Workspace), `privat-beispiel` (persönlich)
   - Agents: `reviewer`
3. Im Chat `/` tippen: `commit-nachricht` und `privat-beispiel` werden
   angeboten.
4. Agent-Auswahl: `reviewer` ist wählbar.
5. Im Chat nach einer Datei in `projekte/beispiel-app/` fragen: In den
   Referenzen erscheint `projekte/beispiel-app/AGENTS.md`.
6. „MCP: List Servers“: `azure-devops` aus `.mcp.json` ist gelistet. Starten,
   mit dem Microsoft-Konto anmelden und im Chat nach den Projekten in
   `gmhgruppe` fragen.
7. Erweiterungen, Filter „@recommended“: Copilot ist empfohlen.
8. Superpowers: „Chat: Open Customizations“ zeigt die Superpowers-Skills
   (z. B. `brainstorming`, `writing-plans`) als Workspace-Skills, und im Chat
   ist `/brainstorming` aufrufbar. Im Terminal meldet
   `python3 tools/superpowers/aktualisieren.py --pruefen` den Stand.
9. Punkte 2 bis 6 und 8 in beiden Agent-Modi wiederholen, soweit die Auswahl
   angeboten wird.
10. Im Terminal `git status`: Der private Skill, `CLAUDE.md` und `.claude/`
    tauchen nicht auf.

## Dem Umsetzer überlassen

- Genauer Wortlaut der Beispielinhalte. Sie müssen kurz und an einem Merkmal
  eindeutig erkennbar sein.
- Gültige Werkzeugnamen im Frontmatter von `reviewer.agent.md` für VS Code
  1.147. Zu prüfen in der Referenz für Agent-Dateien.
- Die genaue ID der Copilot-Erweiterung für `extensions.json`. Auf dem Server
  ist nur `github.copilot` installiert, was auf eine zusammengelegte
  Erweiterung hindeutet.
- Ob VS Code eine eingebaute Übertragung von `.vscode/mcp.json` nach
  `.mcp.json` anbietet. Falls ja, kommt sie in die Anleitung.

## Meine Entscheidungen (bitte prüfen)

Diese Punkte habe ich festgelegt, sie wurden nicht ausdrücklich besprochen:

1. `AGENTS.md` ist die einzige Hauptdatei. `CLAUDE.md` und `.claude/` kommen
   nicht ins Repo (Nutzerentscheidung), sondern in `.gitignore`.
2. Skills liegen in `.agents/skills` statt in `.github/skills`.
3. MCP-Server liegen in `.mcp.json` statt in `.vscode/mcp.json`.
4. Keine Prompt-Dateien, stattdessen Skills.
5. Projektanweisungen als `AGENTS.md` im Projektordner, dazu die
   experimentelle Einstellung für den eingebauten Modus.
6. Hooks werden nur dokumentiert, nicht vorgeführt.
7. Ein privater Beispiel-Skill wird in deinem Home auf diesem Rechner angelegt.
8. Die Anleitung liegt in `docs/genai-rahmen.md`. Sie ist allgemein, die
   Prüfliste für die Demo steht im README.
9. Statt eines Demo-MCP-Servers ist der Remote-MCP-Server von Azure DevOps
   eingetragen (Nutzerentscheidung, Organisation `gmhgruppe`). Meine
   Festlegungen: Remote statt lokal über `npx`, weil Node hier nur pro Nutzer
   über nvm installiert ist und Microsoft den Remote-Server empfiehlt; alle
   Werkzeuge freigegeben, kein `X-MCP-Readonly`.
10. Das Commit-Format im Beispiel-Skill ist ein Platzhalter, den ihr durch
    euer echtes Format ersetzt.
11. Claude Code findet die geteilten Skills und Agents vorerst nicht. Das ist
    so gewollt, solange ihr nur Copilot nutzt.
12. Privates liegt immer im Home, auch für Claude Code. Die Einträge in
    `.gitignore` sind nur ein Sicherheitsnetz.
13. Die Anleitung enthält eine Tabelle, wie man bestehende Copilot-Dateien im
    Monorepo übernimmt.
14. Superpowers liegt als Kopie in `.github/skills/`, getrennt von den eigenen
    Skills in `.agents/skills/` (Weg C1, Trennung per Nachtrag auf Wunsch des
    Nutzers). Meine Festlegungen dazu: Alle 15 Skills werden
    kopiert, nichts wird ausgelassen. Das Skript ist in Python geschrieben und
    holt die Dateien per `git`. Der Stand steht in `tools/superpowers/`, nicht
    im Skill-Ordner. Die Lizenz wird mitkopiert. `AGENTS.md` ersetzt den
    Hook.
15. Das README enthält keinen Abschnitt mehr zu Claude Code.
