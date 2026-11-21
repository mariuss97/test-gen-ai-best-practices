# GenAI-Rahmen (Demo) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dieses Repo zeigt beispielhaft die freigegebene Struktur für geteilte
und private GenAI-Anpassungen (VS Code + Copilot, werkzeugneutral, wo möglich),
mit Prüfliste und Anleitung für das Team.

**Architecture:** Geteilte Anpassungen liegen an den Standardorten im Repo
(`AGENTS.md`, `.agents/skills/`, `.github/agents/`, `.github/instructions/`,
`.mcp.json`, `.vscode/`). Private Anpassungen liegen im Home auf dem
Linux-Rechner. Ein kleiner MCP-Server nur mit der Python-Standardbibliothek
zeigt `.mcp.json`. Die Skills von Superpowers liegen als Kopie in
`.agents/skills/`. Ein Skript (`tools/superpowers/aktualisieren.py`) holt eine
Version per `git` und ersetzt nur die Superpowers-Ordner. Claude-Dateien
bleiben lokal und gitignored. Tests mit `unittest` prüfen Server, Skript und
Struktur.

**Tech Stack:** Markdown mit YAML-Frontmatter, JSON/JSONC, Python 3.10
(nur Standardbibliothek, `unittest`), Git.

**Spec:** `docs/superpowers/specs/2026-11-21-genai-rahmen-design.md`

## Global Constraints

- Alle Dokumentation und alle Beispielinhalte auf Deutsch.
- Ordnernamen genau wie im Spec: `.agents/skills/`, `.github/agents/`, `.github/instructions/`, `.mcp.json`, `.vscode/`. Nicht umbenennen.
- Ziel ist VS Code 1.147.0 auf dem Server. Copilot Chat ist dort eingebaut (`GitHub.copilot-chat` 0.75.0).
- Keine Prompt-Dateien (`.prompt.md`), keine Hooks-Demo, keine Änderung an `.vscode/launch.json`.
- Keine Claude-Dateien einchecken. `CLAUDE.md` und `.claude/` bleiben lokal, kommen in `.gitignore` und werden weder geändert noch gelöscht.
- Keine Geheimnisse und keine persönlichen Daten in eingecheckten Dateien.
- Python nur Standardbibliothek. Der Server läuft mit dem systemweiten `python3` (`/usr/bin/python3`, 3.10).
- Private Dateien liegen nie im Repo. Nur `~/.agents/skills/privat-beispiel/` wird außerhalb des Repos angelegt.
- Skill-Ordnername = `name` im Frontmatter: Kleinbuchstaben, Ziffern und Bindestriche.
- Werkzeuge des Agents `reviewer`: nur `read` und `search` (Werkzeugsets, die VS Code 1.147 und Copilot kennen).
- Superpowers: Quelle `https://github.com/obra/superpowers.git`, Startversion `v7.0.2` (Commit `22f0b463e7a5e579904dd6211a520321035526f7`), alle 15 Skills unverändert kopieren. Superpowers-Dateien nur über das Skript ändern, nie von Hand.
- Kein `.github/copilot/settings.json` und keine Plugin-Empfehlung (durch die Kopie ersetzt).
- Tests laufen mit: `python3 -m unittest discover -s tests -v`. Nur der eine Schritt, der Superpowers wirklich holt, braucht Netz. Die Tests selbst laufen ohne Netz.
- Commit-Nachrichten: `<bereich>: <Beschreibung im Imperativ>`, endend mit `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. Der Server läuft mit `LANG=C`. Erwartet: Der Gruß mit Umlauten kommt unverändert an, und der Server stürzt nicht ab (Test in Task 1).
2. Der Client schickt `notifications/initialized` ohne `id`. Erwartet: keine Antwort, denn eine Antwort bringt Clients durcheinander (Test in Task 1).
3. Eine neue Superpowers-Version bringt einen Skill mit, der so heißt wie ein eigener Skill-Ordner. Erwartet: Abbruch mit Meldung, und nichts im Repo ist verändert (Test in Task 5).
4. Das Holen scheitert (unbekannte Version, kein Netz). Erwartet: Exit-Code 2, Meldung, und nichts im Repo ist verändert (Test in Task 5).
5. Ein privater Skill (`privat-…`) landet versehentlich in Git. Erwartet: Ein Test schlägt fehl (Test in Task 3).

---

## Vorbereitung (vor Task 1)

Auf `main` liegen noch nicht eingecheckte Änderungen des Nutzers (`README.md`,
`.gitignore`, dazu `CLAUDE.md` und `.claude/settings.json`). Eingecheckt werden
nur `README.md` und `.gitignore`. `CLAUDE.md` und `.claude/` bleiben unberührt
und werden nie mit `git add` erfasst.

- [ ] Branch anlegen: `git switch -c genai-rahmen`
- [ ] Ausgangsstand plus Spec und Plan committen (Dateien einzeln nennen, kein `git add -A`):

```bash
git add README.md .gitignore docs/superpowers/
git commit -m "basis: Ausgangsstand und GenAI-Rahmen-Design festhalten"
```

Erwartet: `git status` zeigt nur noch `CLAUDE.md` und `.claude/` als
unversioniert. Task 4 nimmt sie per `.gitignore` aus der Anzeige.

---

### Task 1: Demo-MCP-Server und `.mcp.json`

**Files:**
- Create: `tools/mcp-demo/server.py`
- Create: `.mcp.json`
- Test: `tests/test_mcp_demo.py`

**Interfaces:**
- Consumes: nichts
- Produces: Konstanten in `tools/mcp-demo/server.py`:
  `SERVER_NAME = "genai-demo"`, `TOOL_NAME = "demo_gruss"`,
  `GRUSS = "Hallo aus dem GenAI-Rahmen: Der MCP-Server aus .mcp.json läuft auf dem Linux-Rechner."`,
  `DEFAULT_PROTOCOL_VERSION = "2025-06-18"`. Funktionen
  `handle(message: dict) -> dict | None` und `main() -> None`.
  Der Server-Eintrag in `.mcp.json` heißt `genai-demo`.

- [ ] **Step 1: Write the failing tests** in `tests/test_mcp_demo.py`

Hilfsfunktion `run_server(lines: list[str], env: dict | None = None) -> list[dict]`:
Startet `["python3", "tools/mcp-demo/server.py"]` mit `cwd` = Hauptordner des
Repos, schreibt die Zeilen (jeweils mit `\n`), schließt stdin, wartet höchstens
5 s und gibt die Antwortzeilen als JSON zurück. Tests:

```python
def test_initialize_echoes_client_version(self):
    [r] = run_server([json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}})])
    self.assertEqual(r["id"], 1)
    self.assertEqual(r["result"]["protocolVersion"], "2025-11-25")
    self.assertIn("tools", r["result"]["capabilities"])
    self.assertEqual(r["result"]["serverInfo"]["name"], "genai-demo")

def test_initialize_without_version_uses_default(self):
    # params ohne protocolVersion -> result.protocolVersion == "2025-06-18"

def test_notification_gets_no_response(self):
    # Zeilen: {"jsonrpc":"2.0","method":"notifications/initialized"}, dann ping mit id 7
    # -> genau eine Antwort, mit id 7 und result == {}

def test_tools_list_contains_demo_gruss(self):
    # result.tools hat genau ein Element: name "demo_gruss", description nicht leer,
    # inputSchema == {"type": "object", "properties": {}}

def test_tools_call_returns_gruss_under_lang_c(self):
    # env = os.environ ohne PYTHONIOENCODING, mit LANG=C und LC_ALL=C
    # tools/call {"name": "demo_gruss", "arguments": {}}
    # -> result.content == [{"type": "text", "text": GRUSS}] und result.isError is False

def test_unknown_tool_is_error(self):
    # tools/call name "gibt_es_nicht" -> error.code == -32602

def test_unknown_method_is_error(self):
    # method "foo/bar" mit id -> error.code == -32601

def test_blank_and_broken_lines_keep_server_alive(self):
    # Zeilen: "", "{kaputt", ping id 3
    # -> zwei Antworten: erste error.code == -32700 mit id None, zweite id 3

def test_mcp_json_points_to_server(self):
    # .mcp.json: mcpServers.genai-demo.command == "python3",
    # args == ["tools/mcp-demo/server.py"], und die Datei existiert
```

`GRUSS` im Test als eigenes Literal, damit der Test den Text festhält und ihn
nicht aus dem Server importiert.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_mcp_demo -v`
Expected: FAIL/ERROR (Server-Datei und `.mcp.json` fehlen)

- [ ] **Step 3: Implement `handle(message: dict) -> dict | None` und `main() -> None` in `tools/mcp-demo/server.py`**

`main` liest `sys.stdin` zeilenweise, ignoriert Leerzeilen, beantwortet
kaputtes JSON mit `{"jsonrpc":"2.0","id":null,"error":{"code":-32700,...}}` und
schreibt jede Antwort als `json.dumps(antwort)` (Standard `ensure_ascii=True`,
damit die Ausgabe vom Locale unabhängig ist) plus `\n`, danach `flush()`. Bei
Dateiende endet der Server. `handle` gibt für Nachrichten ohne `id` `None`
zurück und kennt `initialize`, `ping`, `tools/list` und `tools/call`. Sonst
antwortet es mit Fehler -32601. Kopfkommentar der Datei: wofür der Server da
ist, dass er nur zur Demo dient und nur die Standardbibliothek nutzt.

`.mcp.json`:

```json
{
  "mcpServers": {
    "genai-demo": {
      "command": "python3",
      "args": ["tools/mcp-demo/server.py"]
    }
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tests.test_mcp_demo -v`
Expected: alle 9 Tests PASS

- [ ] **Step 5: Commit**

```bash
git add tools/mcp-demo/server.py .mcp.json tests/test_mcp_demo.py
git commit -m "mcp: Demo-Server ohne Abhängigkeiten über .mcp.json anmelden"
```

---

### Task 2: Anweisungen (`AGENTS.md`, Projekt, Markdown-Regeln)

**Files:**
- Create: `tests/hilfen.py`
- Create: `AGENTS.md`
- Create: `projekte/beispiel-app/AGENTS.md`, `projekte/beispiel-app/README.md`
- Create: `.github/instructions/markdown.instructions.md`
- Test: `tests/test_anweisungen.py`

**Interfaces:**
- Consumes: nichts
- Produces: in `tests/hilfen.py`: `REPO: pathlib.Path` (Hauptordner),
  `frontmatter(pfad: pathlib.Path) -> dict[str, str]` (Schlüssel/Wert-Zeilen
  zwischen dem ersten und zweiten `---`, Werte ohne umschließende
  Anführungszeichen) und `jsonc(pfad: pathlib.Path) -> object` (JSON nach
  Entfernen von Zeilen, die mit `//` beginnen, auch eingerückt).

- [ ] **Step 1: Write the failing tests** in `tests/test_anweisungen.py`

```python
def test_agents_md_exists_and_points_to_guide(self):
    text = (REPO / "AGENTS.md").read_text()
    self.assertIn("docs/genai-rahmen.md", text)
    self.assertIn("using-superpowers", text)

def test_project_agents_md_has_marker(self):
    text = (REPO / "projekte/beispiel-app/AGENTS.md").read_text()
    self.assertIn("Regeln aus projekte/beispiel-app/AGENTS.md aktiv.", text)

def test_markdown_instructions_apply_to_md(self):
    fm = frontmatter(REPO / ".github/instructions/markdown.instructions.md")
    self.assertEqual(fm["applyTo"], "**/*.md")
    self.assertTrue(fm["description"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_anweisungen -v`
Expected: FAIL/ERROR (Dateien fehlen)

- [ ] **Step 3: Write the files**

- `tests/hilfen.py`: siehe Interfaces.
- `AGENTS.md`: übernimmt aus der lokalen `CLAUDE.md` Zweck, Sprache und den
  Prüfhinweis, aber keine Claude-spezifischen Sätze. Er beschreibt den Zweck
  des Repos (Spielwiese für einen GenAI-Rahmen mit Copilot in VS Code), legt
  Deutsch fest und sagt, dass geteilte Anpassungen an den Standardorten liegen
  (Verweis auf `docs/genai-rahmen.md`) und Privates nie ins Repo gehört.
  Außerdem: Nach Änderungen an KI-Anpassungen, `.vscode/` oder `AGENTS.md`
  nennt der Agent kurz, was der Nutzer in VS Code prüfen kann (siehe
  `README.md`). Als Ersatz für den Superpowers-Hook: Vor jeder Aufgabe prüfen,
  ob ein Skill passt, und dafür den Skill `using-superpowers` lesen. Die
  Superpowers-Skills unter `.agents/skills/` nicht von Hand ändern (siehe
  `tools/superpowers/stand.json`).
- `projekte/beispiel-app/AGENTS.md`: gilt nur für dieses Beispielprojekt.
  Regel: Antworten zu Dateien in diesem Ordner beginnen mit dem Satz
  „Regeln aus projekte/beispiel-app/AGENTS.md aktiv.“
- `projekte/beispiel-app/README.md`: zwei bis drei Sätze, dass dies ein
  Platzhalter für ein Projekt im Monorepo ist.
- `.github/instructions/markdown.instructions.md`: Frontmatter `description`
  und `applyTo: "**/*.md"`. Inhalt: wenige Stilregeln für Doku (Deutsch, kurze
  Sätze, Überschriften im Satzstil, Tabellen für Gegenüberstellungen).

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tests.test_anweisungen -v`
Expected: 3 Tests PASS

- [ ] **Step 5: Commit**

```bash
git add tests/hilfen.py tests/test_anweisungen.py AGENTS.md projekte/ .github/instructions/
git commit -m "anweisungen: AGENTS.md als Hauptdatei, Projekt- und Markdown-Regeln"
```

---

### Task 3: Skills und Agent (geteilt und privat)

**Files:**
- Create: `.agents/skills/commit-nachricht/SKILL.md`
- Create: `.github/agents/reviewer.agent.md`
- Create (außerhalb des Repos): `~/.agents/skills/privat-beispiel/SKILL.md`
- Test: `tests/test_skills_agents.py`

**Interfaces:**
- Consumes: `REPO`, `frontmatter` aus `tests/hilfen.py` (Task 2)
- Produces: Skill `commit-nachricht`, Agent `reviewer`, privater Skill
  `privat-beispiel` (Namen werden in Task 6 in der Prüfliste genannt)

- [ ] **Step 1: Write the failing tests** in `tests/test_skills_agents.py`

```python
def test_skill_names_match_folders(self):
    skills = sorted((REPO / ".agents/skills").glob("*/SKILL.md"))
    self.assertTrue(skills)
    for s in skills:
        fm = frontmatter(s)
        self.assertEqual(fm["name"], s.parent.name)
        self.assertRegex(fm["name"], r"^[a-z0-9]+(-[a-z0-9]+)*$")
        self.assertTrue(fm["description"])

def test_commit_skill_marks_format_as_example(self):
    text = (REPO / ".agents/skills/commit-nachricht/SKILL.md").read_text()
    self.assertIn("<bereich>: <Beschreibung im Imperativ>", text)
    self.assertIn("Beispiel", text)

def test_reviewer_is_read_only(self):
    fm = frontmatter(REPO / ".github/agents/reviewer.agent.md")
    self.assertTrue(fm["description"])
    tools = set(re.findall(r"[a-z]+", fm["tools"]))
    self.assertEqual(tools, {"read", "search"})

def test_no_private_files_tracked(self):
    out = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True).stdout
    self.assertNotIn("privat-", out)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_skills_agents -v`
Expected: FAIL/ERROR (Dateien fehlen). `test_no_private_files_tracked` besteht schon.

- [ ] **Step 3: Write the files**

- `commit-nachricht/SKILL.md`: Frontmatter `name: commit-nachricht` und eine
  `description`, die sagt, wann der Skill greift (Commit-Nachricht aus den
  aktuellen Änderungen schreiben). Inhalt: die Änderungen ansehen, eine
  Nachricht im Format `<bereich>: <Beschreibung im Imperativ>` schreiben, dann
  eine Leerzeile und Stichpunkte. Deutlich als Beispielformat kennzeichnen,
  das das Team durch sein echtes Format ersetzt. Nicht selbst committen,
  sondern die Nachricht vorschlagen.
- `reviewer.agent.md`: Frontmatter `name: reviewer`, `description`,
  `tools: ['read', 'search']`. Inhalt: prüft Änderungen auf Fehler und
  Verstöße gegen `AGENTS.md`, ändert nichts und antwortet mit einer Liste von
  Befunden, die schwersten zuerst.
- `~/.agents/skills/privat-beispiel/SKILL.md` (mit `mkdir -p` anlegen):
  `name: privat-beispiel`, eine `description` als privates Beispiel. Inhalt:
  antwortet mit „Privater Skill aus ~/.agents/skills aktiv.“ und erklärt in
  einem Satz, dass dieser Skill nur für diesen Nutzer gilt.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tests.test_skills_agents -v && test -f ~/.agents/skills/privat-beispiel/SKILL.md && echo privat-ok`
Expected: 4 Tests PASS, Ausgabe `privat-ok`

- [ ] **Step 5: Commit** (nur Repo-Dateien)

```bash
git add .agents/ .github/agents/ tests/test_skills_agents.py
git commit -m "skills: Beispiel-Skill commit-nachricht und Agent reviewer"
```

---

### Task 4: VS-Code-Dateien und `.gitignore`

**Files:**
- Create: `.vscode/settings.json`, `.vscode/extensions.json`
- Modify: `.gitignore`
- Test: `tests/test_vscode.py`

**Interfaces:**
- Consumes: `REPO`, `jsonc` aus `tests/hilfen.py` (Task 2)
- Produces: nichts, was spätere Tasks aufrufen

- [ ] **Step 1: Write the failing tests** in `tests/test_vscode.py`

```python
def test_settings_enable_nested_agents_md_only(self):
    self.assertEqual(jsonc(REPO / ".vscode/settings.json"), {"chat.useNestedAgentsMdFiles": True})

def test_settings_explain_why(self):
    self.assertIn("//", (REPO / ".vscode/settings.json").read_text())

def test_extensions_recommend_copilot_chat(self):
    self.assertEqual(jsonc(REPO / ".vscode/extensions.json")["recommendations"], ["github.copilot-chat"])

def test_gitignore_entries(self):
    lines = (REPO / ".gitignore").read_text().splitlines()
    for entry in ["CLAUDE.md", "CLAUDE.local.md", ".claude/"]:
        self.assertIn(entry, lines)

def test_claude_files_ignored_and_untracked(self):
    r = subprocess.run(["git", "check-ignore", "-q", "CLAUDE.md", ".claude/settings.json"], cwd=REPO)
    self.assertEqual(r.returncode, 0)
    tracked = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True).stdout.splitlines()
    self.assertFalse([p for p in tracked if p == "CLAUDE.md" or p.startswith(".claude/")])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_vscode -v`
Expected: FAIL/ERROR (`.vscode/` fehlt, Einträge fehlen in `.gitignore`)

- [ ] **Step 3: Write the files**

- `.vscode/settings.json`: nur `chat.useNestedAgentsMdFiles: true`. Darüber
  `//`-Kommentare: Die Einstellung lässt auch den eingebauten Agent-Modus die
  `AGENTS.md` in Projektordnern lesen (experimentell), und in diese Datei
  gehört nur, was für alle gleich sein muss.
- `.vscode/extensions.json`: `{"recommendations": ["github.copilot-chat"]}`.
- `.gitignore`: ganz ersetzen. Ein Kommentar sagt, dass private KI-Anpassungen
  ins Home gehören (Verweis auf `docs/genai-rahmen.md`) und Claude-Dateien
  nicht eingecheckt werden. Danach je eine Zeile `CLAUDE.md`, `CLAUDE.local.md`
  und `.claude/`. Die bisherige Zeile `.claude/settings.local.json` entfällt,
  `.claude/` deckt sie ab.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tests.test_vscode -v && git status --short`
Expected: 5 Tests PASS. `git status --short` zeigt weder `CLAUDE.md` noch `.claude/`.

- [ ] **Step 5: Commit**

```bash
git add .vscode/ .gitignore tests/test_vscode.py
git commit -m "vscode: Team-Einstellungen, Empfehlung und .gitignore"
```

---

### Task 5: Superpowers-Kopie und Update-Skript

**Files:**
- Create: `tools/superpowers/aktualisieren.py`
- Create (vom Skript erzeugt): `tools/superpowers/stand.json`, `tools/superpowers/LICENSE`, `.agents/skills/<15 Superpowers-Skills>/`
- Test: `tests/test_superpowers.py`

**Interfaces:**
- Consumes: `REPO` aus `tests/hilfen.py` (Task 2). Der eigene Skill
  `.agents/skills/commit-nachricht/` (Task 3) muss unberührt bleiben.
- Produces: in `tools/superpowers/aktualisieren.py`:
  `QUELLE = "https://github.com/obra/superpowers.git"`,
  `neueste_version(quelle: str) -> str`,
  `aktualisieren(ziel: Path, quelle: str = QUELLE, version: str | None = None) -> dict`,
  `pruefen(ziel: Path, quelle: str = QUELLE) -> int`,
  `main(argv: list[str] | None = None) -> int`.
  `stand.json` = `{"quelle": str, "version": str, "commit": str, "skills": [str, ...]}`
  (Skills sortiert, 2 Leerzeichen Einrückung, Zeilenumbruch am Ende).
  Aufruf: `python3 tools/superpowers/aktualisieren.py [VERSION] [--pruefen] [--quelle URL] [--ziel PFAD]`.
  `--ziel` ist standardmäßig der Hauptordner des Repos (zwei Ebenen über der
  Skriptdatei). Exit-Codes: 0 = erledigt bzw. aktuell, 1 = neuere Version
  verfügbar (nur bei `--pruefen`), 2 = Fehler (Meldung auf stderr, nichts
  verändert).

- [ ] **Step 1: Write the failing tests** in `tests/test_superpowers.py`

Testgerüst in `setUp`, ohne Netz. Ein temporäres Git-Repo `upstream` bekommt
Commit 1 mit `skills/alpha/SKILL.md`, `skills/beta/SKILL.md`, einer
ausführbaren `skills/beta/scripts/run.sh` und `LICENSE`, dazu die Tags `v1.0.0`
und `v1.2.0`. Commit 2 entfernt `beta` und fügt `skills/gamma/SKILL.md` hinzu,
mit Tag `v1.10.0`. Git-Aufrufe im Gerüst mit `-c user.name=t -c user.email=t@t`.
`quelle = upstream.as_uri()`. Ein temporärer Zielordner `ziel` enthält den
eigenen Skill `.agents/skills/commit-nachricht/SKILL.md`. Hilfsfunktion
`schnappschuss(pfad) -> dict[str, bytes]` liefert alle Dateien darunter.

```python
def test_neueste_version_sorts_numerically(self):
    self.assertEqual(neueste_version(self.quelle), "v1.10.0")

def test_install_copies_skills_and_writes_stand(self):
    aktualisieren(self.ziel, self.quelle, "v1.0.0")
    stand = json.loads((self.ziel / "tools/superpowers/stand.json").read_text())
    self.assertEqual(stand, {"quelle": self.quelle, "version": "v1.0.0",
                             "commit": self.sha_v1_0_0, "skills": ["alpha", "beta"]})
    self.assertTrue((self.ziel / ".agents/skills/alpha/SKILL.md").is_file())
    self.assertTrue((self.ziel / "tools/superpowers/LICENSE").is_file())
    self.assertEqual((self.ziel / ".agents/skills/commit-nachricht/SKILL.md").read_text(), self.eigener_skill_text)

def test_executable_bits_preserved(self):
    # nach v1.0.0: .agents/skills/beta/scripts/run.sh ist ausführbar (os.access X_OK)

def test_update_removes_dropped_skills(self):
    # v1.0.0, dann v1.10.0 -> alpha und gamma da, beta weg, commit-nachricht unverändert,
    # stand.skills == ["alpha", "gamma"]

def test_same_version_twice_is_idempotent(self):
    # zweimal v1.0.0 -> schnappschuss(ziel) danach gleich

def test_conflict_with_own_skill_aborts_without_changes(self):
    # ziel bekommt eigenen Ordner .agents/skills/alpha/ (steht nicht in stand.json)
    # vorher = schnappschuss(ziel); main(["v1.0.0", "--quelle", q, "--ziel", str(ziel)]) == 2
    # schnappschuss(ziel) == vorher

def test_unknown_version_aborts_without_changes(self):
    # main(["v9.9.9", "--quelle", q, "--ziel", str(ziel)]) == 2, schnappschuss unverändert

def test_pruefen_reports_newer_version(self):
    # nach v1.0.0: pruefen(ziel, quelle) == 1; nach v1.10.0: == 0

def test_repo_copy_matches_stand(self):
    # im echten REPO: stand.json version == "v7.0.2",
    # commit == "22f0b463e7a5e579904dd6211a520321035526f7", 15 skills,
    # jeder als .agents/skills/<name>/SKILL.md vorhanden, tools/superpowers/LICENSE vorhanden
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_superpowers -v`
Expected: ERROR (Modul `aktualisieren` fehlt)

- [ ] **Step 3: Implement the functions in `tools/superpowers/aktualisieren.py`**

Ablauf von `aktualisieren`: Erst alles prüfen, dann schreiben.
1. Ohne `version` ruft es `neueste_version` auf. Die liest
   `git ls-remote --tags --refs <quelle> "v*"` und wählt den höchsten Tag nach
   Zahlen (`vX.Y.Z` als Tupel). Andere Tags werden ignoriert.
2. `git clone --quiet --depth 1 --branch <version> <quelle> <tempdir>`, dann
   Commit per `git -C <tempdir> rev-parse HEAD`.
3. Neue Skills sind die Ordner unter `skills/` mit `SKILL.md`. Alte Skills
   stehen in der bisherigen `stand.json` (sonst leer). Gibt es einen neuen
   Skill, dessen Ordner im Ziel schon existiert, aber nicht unter den alten
   steht, folgt Abbruch mit `ValueError`, bevor etwas geschrieben wird.
4. Danach werden alte Ordner gelöscht und neue mit `shutil.copytree` kopiert
   (Rechte bleiben erhalten). `LICENSE` wird nach `tools/superpowers/LICENSE`
   kopiert und `stand.json` geschrieben.

`main` fängt `ValueError` und Fehler aus `subprocess` ab, schreibt eine
deutsche Meldung auf stderr und gibt 2 zurück. Bei Erfolg nennt es Version und
Zahl der Skills und rät zu `git diff --stat`. `pruefen` gibt
„aktuell (vX)“ oder „neuere Version verfügbar: vY (installiert: vX)“ aus.
Kopfkommentar: wofür das Skript da ist und dass die kopierten Dateien nicht
von Hand geändert werden.

- [ ] **Step 4: Run tests to verify the fixture tests pass**

Run: `python3 -m unittest tests.test_superpowers -v`
Expected: alle Tests PASS außer `test_repo_copy_matches_stand` (FAIL, die echte Kopie fehlt noch)

- [ ] **Step 5: Superpowers v7.0.2 wirklich holen** (braucht Netz)

Run: `python3 tools/superpowers/aktualisieren.py v7.0.2 && python3 tools/superpowers/aktualisieren.py --pruefen; echo "exit=$?"`
Expected: Meldung mit `v7.0.2` und 15 Skills, danach `aktuell (v7.0.2)` und
`exit=0`. Ist inzwischen eine neuere Version erschienen, meldet `--pruefen`
sie mit `exit=1`. Das ist kein Fehler: Für diese Demo bleibt es bei `v7.0.2`.

- [ ] **Step 6: Run all tests**

Run: `python3 -m unittest discover -s tests -v`
Expected: alle PASS. `test_skill_names_match_folders` aus Task 3 prüft jetzt
auch die 15 Superpowers-Skills.

- [ ] **Step 7: Commit**

```bash
git add tools/superpowers/ .agents/skills/ tests/test_superpowers.py
git commit -m "superpowers: Skills v7.0.2 als Kopie und Update-Skript"
```

---

### Task 6: Anleitung und README

**Files:**
- Create: `docs/genai-rahmen.md`
- Modify: `README.md` (ganz ersetzen)
- Test: `tests/test_doku.py`

**Interfaces:**
- Consumes: `REPO` aus `tests/hilfen.py`. Namen `commit-nachricht`,
  `privat-beispiel`, `reviewer`, `demo_gruss`, `genai-demo` aus Task 1 und 3.
  Aufruf `tools/superpowers/aktualisieren.py` mit `--pruefen` aus Task 5.
- Produces: nichts

- [ ] **Step 1: Write the failing tests** in `tests/test_doku.py`

```python
def test_relative_links_resolve(self):
    # In README.md und docs/genai-rahmen.md: jeder Markdown-Link [..](ziel),
    # dessen Ziel nicht mit http, # oder mailto beginnt, zeigt (ohne #anker)
    # auf eine existierende Datei relativ zur Datei

def test_guide_has_sections(self):
    text = (REPO / "docs/genai-rahmen.md").read_text()
    for h in ["## Was liegt wo", "## Regeln", "## Private Ordner anlegen",
              "## Prüfen, ob alles erkannt wird", "## Bestehendes im Monorepo übernehmen",
              "## Später Claude Code dazunehmen", "## Superpowers aktualisieren"]:
        self.assertIn(h, text)

def test_guide_has_mkdir_for_private_folders(self):
    text = (REPO / "docs/genai-rahmen.md").read_text()
    self.assertIn("mkdir -p ~/.copilot/instructions ~/.copilot/agents ~/.copilot/hooks ~/.agents/skills", text)

def test_readme_checklist_names_demo_items(self):
    text = (REPO / "README.md").read_text()
    for name in ["commit-nachricht", "privat-beispiel", "reviewer", "genai-demo",
                 "demo_gruss", "projekte/beispiel-app/AGENTS.md", "docs/genai-rahmen.md",
                 "tools/superpowers/aktualisieren.py --pruefen", "/brainstorming"]:
        self.assertIn(name, text)

def test_readme_has_no_claude_code_section(self):
    text = (REPO / "README.md").read_text()
    self.assertNotIn("claude plugin list", text)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_doku -v`
Expected: FAIL/ERROR (`docs/genai-rahmen.md` fehlt)

- [ ] **Step 3: Write the files**

- `docs/genai-rahmen.md`: allgemein formuliert, Abschnitte wie im Test.
  Inhalte stehen im Spec unter „Anleitung für das Team“: die Tabellen
  „Geteilt“ und „Privat“, die Regeln, die Tabelle zum Übernehmen, die
  Übertragungstabelle nach Claude Code und Punkt 7 „Superpowers
  aktualisieren“ (prüfen, aktualisieren, Diff und Release-Notes ansehen,
  committen, Pull Request; zurück auf eine ältere Version mit deren Tag).
  Dazu ein Satz, warum es eine Kopie ist und kein Plugin: keine Einrichtung,
  gleiche Version für alle, Updates als prüfbarer Diff. Dazu die Rangfolge der Einstellungen
  aus „Rahmenbedingungen“ und der Pfad der Remote-Einstellungen auf dem
  Server: `~/.vscode-server/data/Machine/settings.json`. Demo-Dateien höchstens
  als Beispiel nennen. Bietet VS Code 1.147 einen Befehl, der `.vscode/mcp.json`
  nach `.mcp.json` überträgt (der Quellcode in `workspaceDotMcpDiscovery.ts`
  erwähnt eine Migration; in der Befehlspalette nach „MCP“ suchen oder im
  Quellcode `src/vs/workbench/contrib/mcp/` unter Tag `1.147.0` nachsehen), dann
  diesen Befehl in der Tabelle zum Übernehmen nennen. Sonst bleibt es beim
  Übertragen von Hand.
- `README.md`: Zweck des Repos (ein bis zwei Sätze), eine Tabelle „Was
  eingerichtet ist“ mit allen Demo-Dateien aus dem Spec, ein Link zur
  Anleitung und die Prüfliste aus dem Spec unter „Prüfliste für die Demo“,
  Punkte 1 bis 10, mit den konkreten Namen. Beim Punkt Erweiterungen steht
  „GitHub Copilot Chat“. Beim Punkt „Chat: Open Customizations“ steht ein
  Hinweis: Wer lokal eine `CLAUDE.md` hat, sieht sie dort zusätzlich, weil VS
  Code sie im eingebauten Modus liest. Das betrifft nur diesen einen Rechner.
  Die bisherigen Claude-Code-Prüfungen (`/super`, `claude plugin list`)
  entfallen. Die Voraussetzungen bleiben: Remote-SSH,
  diesen Ordner öffnen, die Copilot-Chat-Erweiterung auf der SSH-Seite, nach
  Änderungen eine neue Chat-Sitzung starten.

- [ ] **Step 4: Run all tests**

Run: `python3 -m unittest discover -s tests -v`
Expected: alle Tests aus Task 1 bis 6 PASS

- [ ] **Step 5: Commit**

```bash
git add docs/genai-rahmen.md README.md tests/test_doku.py
git commit -m "doku: Anleitung für das Team und Prüfliste für die Demo"
```

---

## Abschluss

- [ ] `python3 -m unittest discover -s tests -v`: alle Tests PASS
- [ ] `git status`: sauber. `git ls-files | grep -E "privat-|^CLAUDE.md$|^\.claude/"` liefert nichts
- [ ] `python3 tools/superpowers/aktualisieren.py --pruefen` meldet den Stand
- [ ] Dem Nutzer nennen, was er in VS Code prüfen kann. Das ist die Prüfliste
      im README, besonders die Superpowers-Skills unter „Chat: Open
      Customizations“ und `/brainstorming`.
