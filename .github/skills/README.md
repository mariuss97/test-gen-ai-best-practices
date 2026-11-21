# Fremde Skills

Dieser Ordner enthält nur Skills aus fremden Quellen, heute die Skills von
[Superpowers](https://github.com/obra/superpowers) (Lizenz MIT). Die Quellen
stehen in `tools/external-skills/sources.json`, die Lizenzen unter
`tools/external-skills/licenses/<quelle>/LICENSE`. Welche Ordner zu welcher Quelle
gehören und welche Version installiert ist, steht in
`tools/external-skills/lock.json`.

- Nicht von Hand ändern. Das nächste Update überschreibt die Änderungen.
- Aktualisieren nur mit `python3 tools/external-skills/update.py`, dann
  `git diff --stat` prüfen und committen.
- Eigene Skills gehören nach `.agents/skills/`.
