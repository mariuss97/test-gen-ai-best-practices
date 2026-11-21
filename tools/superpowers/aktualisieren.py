#!/usr/bin/env python3
"""Holt die Skills des Open-Source-Plugins Superpowers (MIT) als Kopie ins Repo.

Die Skills landen in `.agents/skills/` neben den eigenen Skills. Version und
Commit stehen in `tools/superpowers/stand.json`, die Lizenz in
`tools/superpowers/LICENSE`. Ein Update läuft bewusst von Hand: Skript starten,
mit `git diff --stat` prüfen, committen.

Die kopierten Dateien werden nicht von Hand geändert, sondern nur mit diesem
Skript erneuert.

Aufruf: python3 tools/superpowers/aktualisieren.py [VERSION] [--pruefen]
                                                   [--quelle URL] [--ziel PFAD]
Exit-Codes: 0 = erledigt bzw. aktuell, 1 = neuere Version verfügbar
(nur bei --pruefen), 2 = Fehler.

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

QUELLE = "https://github.com/obra/superpowers.git"
STAND = "tools/superpowers/stand.json"
LIZENZ = "tools/superpowers/LICENSE"
SKILLS = ".agents/skills"
NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
WEG_ZURUECK = ("Das Repo kann teilweise geändert sein. Zurück geht es mit "
               "`git restore -- .agents/skills tools/superpowers`; mit `git status` "
               "neue, nicht versionierte Ordner prüfen.")


def _verschieben(quelle, ziel):
    os.rename(quelle, ziel)


def _pruefe_namen(namen, woher):
    for n in namen:
        if not isinstance(n, str) or not NAME.fullmatch(n):
            raise ValueError(f"Ungültiger Skill-Name in {woher}: {n!r} "
                             "(erlaubt: Kleinbuchstaben, Ziffern, Bindestriche).")


def _tauschen(ziel: Path, klon: Path, alt, neu, stand_text):
    """Neue Kopie in Staging vorbereiten, dann tauschen; bei Fehler zurückrollen."""
    skills = ziel / SKILLS
    skills.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=ziel / ".agents"))
    erledigt = []  # Rückgängig-Liste: (von, nach)

    def bewegen(von, nach):
        _verschieben(von, nach)
        erledigt.append((von, nach))

    try:
        try:
            for name in neu:
                shutil.copytree(klon / "skills" / name, staging / "neu" / name)
            shutil.copy2(klon / "LICENSE", staging / "LICENSE")
            (staging / "stand.json").write_text(stand_text, encoding="utf-8")
            (staging / "alt").mkdir()
            (ziel / LIZENZ).parent.mkdir(parents=True, exist_ok=True)
            for name in alt:
                if (skills / name).exists():
                    bewegen(skills / name, staging / "alt" / name)
            for name in neu:
                bewegen(staging / "neu" / name, skills / name)
            for datei, pfad in (("LICENSE", ziel / LIZENZ), ("stand.json", ziel / STAND)):
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


def _alter_stand(ziel: Path) -> dict:
    pfad = ziel / STAND
    if pfad.is_file():
        return json.loads(pfad.read_text(encoding="utf-8"))
    return {}


def aktualisieren(ziel: Path, quelle: str = QUELLE, version: str | None = None) -> dict:
    ziel = Path(ziel)
    if version is None:
        version = neueste_version(quelle)
    with tempfile.TemporaryDirectory() as tmp:
        klon = Path(tmp) / "klon"
        try:
            _git("clone", "--quiet", "--depth", "1", "--branch", version, quelle, str(klon))
        except subprocess.CalledProcessError as fehler:
            raise ValueError(
                f"Version {version} aus {quelle} nicht abrufbar: {fehler.stderr.strip()}"
            ) from fehler
        commit = _git("-C", str(klon), "rev-parse", "HEAD")
        neu = sorted(p.parent.name for p in (klon / "skills").glob("*/SKILL.md"))
        if not neu:
            raise ValueError(f"Keine Skills unter skills/ in {version} gefunden.")
        if not (klon / "LICENSE").is_file():
            raise ValueError(f"Keine LICENSE in {version} gefunden.")
        alt = _alter_stand(ziel).get("skills", [])
        _pruefe_namen(alt, STAND)
        _pruefe_namen(neu, f"{version}/skills")

        # Erst alles prüfen ...
        konflikte = [n for n in neu if (ziel / SKILLS / n).exists() and n not in alt]
        if konflikte:
            raise ValueError(
                "Eigene Skills mit gleichem Namen vorhanden, Abbruch: " + ", ".join(konflikte)
            )

        # ... dann schreiben (Staging, Tausch, Rollback).
        stand = {"quelle": quelle, "version": version, "commit": commit, "skills": neu}
        _tauschen(ziel, klon, alt, neu, json.dumps(stand, indent=2) + "\n")
    return stand


def pruefen(ziel: Path, quelle: str = QUELLE) -> int:
    installiert = _alter_stand(Path(ziel)).get("version")
    neueste = neueste_version(quelle)
    if installiert is not None and _versionsnummer(installiert) is not None \
            and _versionsnummer(installiert) >= _versionsnummer(neueste):
        print(f"aktuell ({installiert})")
        return 0
    print(f"neuere Version verfügbar: {neueste} (installiert: {installiert or 'keine'})")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Superpowers-Skills als Kopie ins Repo holen.")
    parser.add_argument("version", nargs="?", help="Tag, z. B. v7.0.2 (Standard: neueste)")
    parser.add_argument("--pruefen", action="store_true",
                        help="nur prüfen, ob eine neuere Version existiert")
    parser.add_argument("--quelle", default=QUELLE, help="Git-URL der Quelle")
    parser.add_argument("--ziel", type=Path, default=Path(__file__).resolve().parents[2],
                        help="Hauptordner des Repos")
    args = parser.parse_args(argv)
    try:
        if args.pruefen:
            return pruefen(args.ziel, args.quelle)
        stand = aktualisieren(args.ziel, args.quelle, args.version)
    except (ValueError, OSError, subprocess.CalledProcessError) as fehler:
        meldung = getattr(fehler, "stderr", None) or fehler
        print(f"Fehler: {str(meldung).strip()}", file=sys.stderr)
        return 2
    print(f"Superpowers {stand['version']} kopiert ({len(stand['skills'])} Skills). "
          "Mit `git diff --stat` prüfen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
