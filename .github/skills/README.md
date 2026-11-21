# Fremde Skills

Dieser Ordner enthält nur Skills aus fremden Quellen, heute die Skills von
[Superpowers](https://github.com/obra/superpowers) (Lizenz MIT). Die Quellen
stehen in `tools/fremde-skills/quellen.json`, die Lizenzen unter
`tools/fremde-skills/lizenzen/<quelle>/LICENSE`. Welche Ordner zu welcher Quelle
gehören und welche Version installiert ist, steht in
`tools/fremde-skills/stand.json`.

- Nicht von Hand ändern. Das nächste Update überschreibt die Änderungen.
- Aktualisieren nur mit `python3 tools/fremde-skills/aktualisieren.py`, dann
  `git diff --stat` prüfen und committen.
- Eigene Skills gehören nach `.agents/skills/`.
