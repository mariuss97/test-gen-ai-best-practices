# External skills

This folder contains only skills from external sources, today the skills from
[Superpowers](https://github.com/obra/superpowers) (MIT license). The sources
are listed in `tools/external-skills/sources.json`, the licenses are under
`tools/external-skills/licenses/<source>/LICENSE`. Which folders belong to
which source and which version is installed is recorded in
`tools/external-skills/lock.json`.

- Do not edit by hand. The next update overwrites your changes.
- Update only with `python3 tools/external-skills/update.py`, then check
  `git diff --stat` and commit.
- Own skills belong in `.agents/skills/`.
