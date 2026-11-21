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
(nur bei --pruefen), 2 = Fehler (nichts verändert).
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

QUELLE = "https://github.com/obra/superpowers.git"
STAND = "tools/superpowers/stand.json"
LIZENZ = "tools/superpowers/LICENSE"
SKILLS = ".agents/skills"


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

        # Erst alles prüfen ...
        konflikte = [n for n in neu if (ziel / SKILLS / n).exists() and n not in alt]
        if konflikte:
            raise ValueError(
                "Eigene Skills mit gleichem Namen vorhanden, Abbruch: " + ", ".join(konflikte)
            )

        # ... dann schreiben.
        for name in alt:
            shutil.rmtree(ziel / SKILLS / name, ignore_errors=True)
        (ziel / SKILLS).mkdir(parents=True, exist_ok=True)
        for name in neu:
            shutil.copytree(klon / "skills" / name, ziel / SKILLS / name)
        (ziel / LIZENZ).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(klon / "LICENSE", ziel / LIZENZ)
        stand = {"quelle": quelle, "version": version, "commit": commit, "skills": neu}
        (ziel / STAND).write_text(json.dumps(stand, indent=2) + "\n", encoding="utf-8")
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
