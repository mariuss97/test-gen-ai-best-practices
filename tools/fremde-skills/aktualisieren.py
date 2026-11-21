#!/usr/bin/env python3
"""Holt Skills fremder Quellen (z. B. Superpowers, MIT) als Kopie ins Repo.

Die Quellen stehen von Hand gepflegt in `tools/fremde-skills/quellen.json`. Die
Skills landen flach in `.github/skills/`, getrennt von den eigenen Skills in
`.agents/skills/`. Version und Commit je Quelle stehen in
`tools/fremde-skills/stand.json` (nur vom Skript geschrieben), die Lizenzen in
`tools/fremde-skills/lizenzen/<quelle>/LICENSE`. Ein Update läuft bewusst von
Hand: Skript starten, mit `git diff --stat` prüfen, committen.

Optionale Schlüssel je Quelle in `quellen.json`: `pfad` (Standard `skills`),
`lizenz` (Standard `LICENSE`), `nur` (nur diese Skills übernehmen) und
`auslassen` (diese Skills nicht übernehmen). `nur` und `auslassen` gehen nicht
zusammen.

Die kopierten Dateien werden nicht von Hand geändert, sondern nur mit diesem
Skript erneuert.

Aufruf: python3 tools/fremde-skills/aktualisieren.py [QUELLE [VERSION]]
                                                     [--pruefen] [--ziel PFAD]
Ohne QUELLE werden alle Quellen bearbeitet. Die URL kommt immer aus
`quellen.json`. Exit-Codes: 0 = erledigt bzw. aktuell, 1 = neuere Version
verfügbar (nur bei --pruefen), 2 = Fehler.

Bei Fehlern vor dem Schreiben bleibt alles unverändert. Geschrieben wird über
einen Staging-Ordner neben dem Ziel; scheitert der Tausch, wird zurückgerollt.
Gelingt auch das nicht, sagt die Fehlermeldung ehrlich, dass das Repo teilweise
geändert sein kann, und nennt den Weg zurück (`git restore`).
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

QUELLEN = "tools/fremde-skills/quellen.json"   # von Hand gepflegt
STAND = "tools/fremde-skills/stand.json"       # nur vom Skript geschrieben
LIZENZEN = "tools/fremde-skills/lizenzen"      # <quelle>/LICENSE
SKILLS = ".github/skills"   # fremde Skills (nur dieses Skript schreibt hier)
EIGENE = ".agents/skills"   # eigene Skills des Teams (werden nie angefasst)
NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
WEG_ZURUECK = ("Das Repo kann teilweise geändert sein. Zurück geht es mit "
               "`git restore -- .github/skills tools/fremde-skills`; mit `git status` "
               "neue, nicht versionierte Ordner prüfen.")


def _verschieben(quelle, ziel):
    os.rename(quelle, ziel)


def _pruefe_namen(namen, woher):
    for n in namen:
        if not isinstance(n, str) or not NAME.fullmatch(n):
            raise ValueError(f"Ungültiger Skill-Name in {woher}: {n!r} "
                             "(erlaubt: Kleinbuchstaben, Ziffern, Bindestriche).")


def _tauschen(ziel: Path, klon: Path, quelle: dict, name: str, alt, neu, stand_text):
    """Neue Kopie in Staging vorbereiten, dann tauschen; bei Fehler zurückrollen."""
    skills = ziel / SKILLS
    skills.mkdir(parents=True, exist_ok=True)
    lizenz_ziel = ziel / LIZENZEN / name / "LICENSE"
    staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=skills.parent))
    erledigt = []  # Rückgängig-Liste: (von, nach)

    def bewegen(von, nach):
        _verschieben(von, nach)
        erledigt.append((von, nach))

    try:
        try:
            for skill in neu:
                shutil.copytree(klon / quelle["pfad"] / skill, staging / "neu" / skill)
            shutil.copy2(klon / quelle["lizenz"], staging / "LICENSE")
            (staging / "stand.json").write_text(stand_text, encoding="utf-8")
            (staging / "alt").mkdir()
            lizenz_ziel.parent.mkdir(parents=True, exist_ok=True)
            (ziel / STAND).parent.mkdir(parents=True, exist_ok=True)
            for skill in alt:
                if (skills / skill).exists():
                    bewegen(skills / skill, staging / "alt" / skill)
            for skill in neu:
                bewegen(staging / "neu" / skill, skills / skill)
            for datei, pfad in (("LICENSE", lizenz_ziel), ("stand.json", ziel / STAND)):
                if pfad.exists():
                    bewegen(pfad, staging / "alt" / ("datei-" + datei))
                bewegen(staging / datei, pfad)
        except BaseException as fehler:
            gescheitert = []
            for von, nach in reversed(erledigt):
                try:
                    _verschieben(nach, von)
                except OSError as e:
                    gescheitert.append(f"{nach}: {e}")
            if gescheitert:
                raise OSError(f"{fehler}. Zurückrollen unvollständig. {WEG_ZURUECK}") from fehler
            raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def _git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True,
                          text=True).stdout.strip()


def _versionsnummer(tag):
    """`v1.10.0` -> (1, 10, 0); alles andere -> None."""
    if not tag.startswith("v"):
        return None
    teile = tag[1:].split(".")
    if len(teile) != 3 or not all(t.isdigit() for t in teile):
        return None
    return tuple(int(t) for t in teile)


def neueste_version(quelle: str) -> str:
    ausgabe = _git("ls-remote", "--tags", "--refs", quelle, "v*")
    tags = []
    for zeile in ausgabe.splitlines():
        tag = zeile.split("\t")[-1].removeprefix("refs/tags/")
        nummer = _versionsnummer(tag)
        if nummer is not None:
            tags.append((nummer, tag))
    if not tags:
        raise ValueError(f"Keine Versions-Tags (vX.Y.Z) in {quelle} gefunden.")
    return max(tags)[1]


def _lade_json(pfad: Path, was: str) -> dict:
    if not pfad.is_file():
        raise ValueError(f"{was} fehlt: {pfad}")
    try:
        daten = json.loads(pfad.read_text(encoding="utf-8"))
    except ValueError as fehler:
        raise ValueError(f"{was} ist kein gültiges JSON: {fehler}") from fehler
    if not isinstance(daten, dict):
        raise ValueError(f"{was} muss ein JSON-Objekt sein.")
    return daten


def _alter_stand(ziel: Path) -> dict:
    pfad = ziel / STAND
    return _lade_json(pfad, STAND) if pfad.is_file() else {}


def _liste(wert, schluessel, name):
    if not isinstance(wert, list):
        raise ValueError(f"`{schluessel}` der Quelle {name} muss eine Liste sein.")
    _pruefe_namen(wert, f"`{schluessel}` der Quelle {name}")
    return wert


def _quelle(ziel: Path, name: str) -> dict:
    """Eintrag aus quellen.json, geprüft und mit Standardwerten ergänzt."""
    if not isinstance(name, str) or not NAME.fullmatch(name):
        raise ValueError(f"Ungültiger Quellname: {name!r} "
                         "(erlaubt: Kleinbuchstaben, Ziffern, Bindestriche).")
    quellen = _lade_json(ziel / QUELLEN, QUELLEN)
    if name not in quellen:
        raise ValueError(f"Quelle {name!r} steht nicht in {QUELLEN} "
                         f"(vorhanden: {', '.join(sorted(quellen)) or 'keine'}).")
    roh = quellen[name]
    if not isinstance(roh, dict) or not isinstance(roh.get("url"), str) or not roh["url"]:
        raise ValueError(f"Quelle {name} in {QUELLEN} braucht eine `url`.")
    eintrag = {"url": roh["url"], "pfad": roh.get("pfad", "skills"),
               "lizenz": roh.get("lizenz", "LICENSE")}
    for schluessel in ("pfad", "lizenz"):
        pfad = Path(str(eintrag[schluessel]))
        if not isinstance(eintrag[schluessel], str) or not eintrag[schluessel] \
                or pfad.is_absolute() or ".." in pfad.parts:
            raise ValueError(f"`{schluessel}` der Quelle {name} muss ein relativer Pfad "
                             "innerhalb der Quelle sein.")
    if "nur" in roh and "auslassen" in roh:
        raise ValueError(f"Quelle {name}: `nur` und `auslassen` gehen nicht zusammen.")
    for schluessel in ("nur", "auslassen"):
        if schluessel in roh:
            eintrag[schluessel] = _liste(roh[schluessel], schluessel, name)
    return eintrag


def aktualisieren(ziel: Path, name: str, version: str | None = None) -> dict:
    ziel = Path(ziel)
    quelle = _quelle(ziel, name)
    url = quelle["url"]
    if version is None:
        version = neueste_version(url)
    with tempfile.TemporaryDirectory() as tmp:
        klon = Path(tmp) / "klon"
        try:
            _git("clone", "--quiet", "--depth", "1", "--branch", version, url, str(klon))
        except subprocess.CalledProcessError as fehler:
            raise ValueError(
                f"Version {version} aus {url} nicht abrufbar: {fehler.stderr.strip()}"
            ) from fehler
        commit = _git("-C", str(klon), "rev-parse", "HEAD")
        if not (klon / quelle["pfad"]).is_dir():
            raise ValueError(f"Ordner {quelle['pfad']} in {name} {version} nicht gefunden.")
        if not (klon / quelle["lizenz"]).is_file():
            raise ValueError(f"Lizenzdatei {quelle['lizenz']} in {name} {version} nicht gefunden.")
        vorhanden = sorted(p.parent.name for p in (klon / quelle["pfad"]).glob("*/SKILL.md"))
        _pruefe_namen(vorhanden, f"{name} {version}/{quelle['pfad']}")
        for schluessel in ("nur", "auslassen"):
            fehlen = [n for n in quelle.get(schluessel, []) if n not in vorhanden]
            if fehlen:
                raise ValueError(f"`{schluessel}` der Quelle {name} nennt Skills, die es in "
                                 f"{version} nicht gibt: {', '.join(fehlen)}")
        neu = [n for n in vorhanden
               if ("nur" not in quelle or n in quelle["nur"]) and n not in quelle.get("auslassen", [])]
        if not neu:
            raise ValueError(f"Keine Skills aus {name} {version} zu übernehmen.")

        stand = _alter_stand(ziel)
        alt = stand.get(name, {}).get("skills", [])
        _pruefe_namen(alt, f"{STAND} ({name})")

        # Erst alles prüfen ...
        eigene = [n for n in neu if (ziel / EIGENE / n).exists()]
        if eigene:
            raise ValueError(
                f"Eigene Skills in {EIGENE} mit gleichem Namen vorhanden, Abbruch: "
                + ", ".join(eigene)
            )
        for andere, eintrag in stand.items():
            if andere == name:
                continue
            doppelt = [n for n in neu if n in eintrag.get("skills", [])]
            if doppelt:
                raise ValueError(
                    f"Skills {', '.join(doppelt)} gibt es in den Quellen {andere} und {name}, "
                    f"Abbruch. In {QUELLEN} bei {name} mit `auslassen` ausnehmen.")
        unbekannt = [n for n in neu if (ziel / SKILLS / n).exists() and n not in alt]
        if unbekannt:
            raise ValueError(
                f"Ordner in {SKILLS}, die nicht zu {name} gehören, Abbruch: "
                + ", ".join(unbekannt)
            )

        # ... dann schreiben (Staging, Tausch, Rollback).
        eintrag = {"url": url, "version": version, "commit": commit, "skills": neu}
        neuer_stand = {**stand, name: eintrag}
        stand_text = json.dumps(dict(sorted(neuer_stand.items())), indent=2,
                                ensure_ascii=False) + "\n"
        _tauschen(ziel, klon, quelle, name, alt, neu, stand_text)
    return eintrag


def _alle_namen(ziel: Path) -> list[str]:
    return sorted(_lade_json(ziel / QUELLEN, QUELLEN))


def pruefen(ziel: Path, name: str | None = None) -> int:
    ziel = Path(ziel)
    namen = _alle_namen(ziel) if name is None else [name]
    stand = _alter_stand(ziel)
    code = 0
    for n in namen:
        quelle = _quelle(ziel, n)
        installiert = stand.get(n, {}).get("version")
        neueste = neueste_version(quelle["url"])
        if installiert is not None and _versionsnummer(installiert) is not None \
                and _versionsnummer(installiert) >= _versionsnummer(neueste):
            print(f"{n}: aktuell ({installiert})")
        else:
            print(f"{n}: neuere Version verfügbar: {neueste} "
                  f"(installiert: {installiert or 'keine'})")
            code = 1
    return code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Skills fremder Quellen als Kopie ins Repo holen.")
    parser.add_argument("quelle", nargs="?",
                        help="Name aus quellen.json (Standard: alle Quellen)")
    parser.add_argument("version", nargs="?",
                        help="Tag, z. B. v7.0.2 (Standard: neueste; nur mit QUELLE)")
    parser.add_argument("--pruefen", action="store_true",
                        help="nur prüfen, ob eine neuere Version existiert")
    parser.add_argument("--ziel", type=Path, default=Path(__file__).resolve().parents[2],
                        help="Hauptordner des Repos")
    args = parser.parse_args(argv)
    fertig = []
    try:
        if args.pruefen:
            return pruefen(args.ziel, args.quelle)
        namen = [args.quelle] if args.quelle else _alle_namen(args.ziel)
        for name in namen:
            stand = aktualisieren(args.ziel, name, args.version)
            fertig.append(name)
            print(f"{name} {stand['version']} kopiert ({len(stand['skills'])} Skills). "
                  "Mit `git diff --stat` prüfen.")
    except (ValueError, OSError, subprocess.CalledProcessError) as fehler:
        meldung = getattr(fehler, "stderr", None) or fehler
        print(f"Fehler: {str(meldung).strip()}", file=sys.stderr)
        if fertig and len(namen) > 1:
            print(f"Schon aktualisiert: {', '.join(fertig)}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
