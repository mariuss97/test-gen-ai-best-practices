# Fremde Skills

Dieser Ordner enthält nur Skills aus fremden Quellen, heute die Skills von
[Superpowers](https://github.com/obra/superpowers) (Lizenz MIT, siehe
`tools/superpowers/LICENSE`). Welche Ordner dazugehören und welche Version
installiert ist, steht in `tools/superpowers/stand.json`.

- Nicht von Hand ändern. Das nächste Update überschreibt die Änderungen.
- Aktualisieren nur mit `python3 tools/superpowers/aktualisieren.py`, dann
  `git diff --stat` prüfen und committen.
- Eigene Skills gehören nach `.agents/skills/`.
