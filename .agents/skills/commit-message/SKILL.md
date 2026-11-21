---
name: commit-message
description: Schreibt eine Commit-Nachricht aus den aktuellen Änderungen. Verwenden, wenn der Nutzer um eine Commit-Nachricht bittet oder fragt, wie er seine Änderungen beschreiben soll.
---

# Commit-Nachricht schreiben

Dieser Skill ist ein Beispiel. Das Format unten ist nur ein Beispielformat;
das Team ersetzt es durch sein echtes Format.

## Vorgehen

1. Die aktuellen Änderungen ansehen (`git status`, `git diff`, bei gestagten
   Änderungen `git diff --staged`).
2. Eine Nachricht im folgenden Beispielformat schreiben:

   ```text
   <bereich>: <Beschreibung im Imperativ>

   - Stichpunkt zu einer wichtigen Änderung
   - Stichpunkt zu einer weiteren Änderung
   ```

   Zwischen Betreffzeile und Stichpunkten steht eine Leerzeile.

3. Beispiel:

   ```text
   docs: Anleitung für Remote-SSH ergänzen

   - Prüfliste für VS Code hinzugefügt
   - Hinweis zu Skills im Home-Verzeichnis ergänzt
   ```

## Wichtig

Nicht selbst committen. Die Nachricht nur vorschlagen und dem Nutzer
überlassen, ob und wann er sie verwendet.
