"""Gemeinsame Hilfen für die Tests."""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def frontmatter(pfad):
    """Liest die Schlüssel/Wert-Zeilen zwischen dem ersten und zweiten `---`."""
    zeilen = Path(pfad).read_text(encoding="utf-8").splitlines()
    if not zeilen or zeilen[0].strip() != "---":
        return {}
    daten = {}
    for zeile in zeilen[1:]:
        if zeile.strip() == "---":
            break
        if ":" not in zeile:
            continue
        schluessel, wert = zeile.split(":", 1)
        wert = wert.strip()
        if len(wert) >= 2 and wert[0] == wert[-1] and wert[0] in "\"'":
            wert = wert[1:-1]
        daten[schluessel.strip()] = wert
    return daten


def jsonc(pfad):
    """Liest JSON und ignoriert Zeilen, die mit `//` beginnen (auch eingerückt)."""
    zeilen = Path(pfad).read_text(encoding="utf-8").splitlines()
    return json.loads("\n".join(z for z in zeilen if not z.lstrip().startswith("//")))
