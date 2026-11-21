"""Tests für das Update-Skript der Superpowers-Kopie (offline, mit Fixture-Repo)."""

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.hilfen import REPO

_SPEC = importlib.util.spec_from_file_location(
    "aktualisieren", REPO / "tools/superpowers/aktualisieren.py"
)
_MODUL = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODUL)
neueste_version = _MODUL.neueste_version
aktualisieren = _MODUL.aktualisieren
pruefen = _MODUL.pruefen
main = _MODUL.main

GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t",
       "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false"]


def git(cwd, *args):
    return subprocess.run(GIT + list(args), cwd=cwd, check=True,
                          capture_output=True, text=True).stdout.strip()


def schnappschuss(pfad):
    """Alle Dateien unter pfad (relativer Pfad -> Inhalt)."""
    pfad = Path(pfad)
    return {str(p.relative_to(pfad)): p.read_bytes()
            for p in sorted(pfad.rglob("*")) if p.is_file()}


class SuperpowersTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        tmp = Path(self._tmp.name)
        up = self.upstream = tmp / "upstream"
        (up / "skills/alpha").mkdir(parents=True)
        (up / "skills/beta/scripts").mkdir(parents=True)
        (up / "skills/alpha/SKILL.md").write_text("alpha\n")
        (up / "skills/beta/SKILL.md").write_text("beta\n")
        run = up / "skills/beta/scripts/run.sh"
        run.write_text("#!/bin/sh\n")
        run.chmod(0o755)
        (up / "LICENSE").write_text("MIT\n")
        git(up, "init", "--quiet")
        git(up, "add", ".")
        git(up, "commit", "--quiet", "-m", "eins")
        self.sha_v1_0_0 = git(up, "rev-parse", "HEAD")
        git(up, "tag", "v1.0.0")
        git(up, "tag", "v1.2.0")
        git(up, "rm", "--quiet", "-r", "skills/beta")
        (up / "skills/gamma").mkdir()
        (up / "skills/gamma/SKILL.md").write_text("gamma\n")
        git(up, "add", ".")
        git(up, "commit", "--quiet", "-m", "zwei")
        git(up, "tag", "v1.10.0")
        self.quelle = up.as_uri()

        self.ziel = tmp / "ziel"
        eigen = self.ziel / ".agents/skills/commit-nachricht"
        eigen.mkdir(parents=True)
        self.eigener_skill_text = "eigener skill\n"
        (eigen / "SKILL.md").write_text(self.eigener_skill_text)

    def test_neueste_version_sorts_numerically(self):
        self.assertEqual(neueste_version(self.quelle), "v1.10.0")

    def test_install_copies_skills_and_writes_stand(self):
        aktualisieren(self.ziel, self.quelle, "v1.0.0")
        stand = json.loads((self.ziel / "tools/superpowers/stand.json").read_text())
        self.assertEqual(stand, {"quelle": self.quelle, "version": "v1.0.0",
                                 "commit": self.sha_v1_0_0, "skills": ["alpha", "beta"]})
        self.assertTrue((self.ziel / ".agents/skills/alpha/SKILL.md").is_file())
        self.assertTrue((self.ziel / "tools/superpowers/LICENSE").is_file())
        self.assertEqual(
            (self.ziel / ".agents/skills/commit-nachricht/SKILL.md").read_text(),
            self.eigener_skill_text)

    def test_executable_bits_preserved(self):
        aktualisieren(self.ziel, self.quelle, "v1.0.0")
        self.assertTrue(os.access(self.ziel / ".agents/skills/beta/scripts/run.sh", os.X_OK))

    def test_update_removes_dropped_skills(self):
        aktualisieren(self.ziel, self.quelle, "v1.0.0")
        aktualisieren(self.ziel, self.quelle, "v1.10.0")
        skills = self.ziel / ".agents/skills"
        self.assertTrue((skills / "alpha/SKILL.md").is_file())
        self.assertTrue((skills / "gamma/SKILL.md").is_file())
        self.assertFalse((skills / "beta").exists())
        self.assertEqual((skills / "commit-nachricht/SKILL.md").read_text(),
                         self.eigener_skill_text)
        stand = json.loads((self.ziel / "tools/superpowers/stand.json").read_text())
        self.assertEqual(stand["skills"], ["alpha", "gamma"])

    def test_same_version_twice_is_idempotent(self):
        aktualisieren(self.ziel, self.quelle, "v1.0.0")
        davor = schnappschuss(self.ziel)
        aktualisieren(self.ziel, self.quelle, "v1.0.0")
        self.assertEqual(schnappschuss(self.ziel), davor)

    def _fehler(self, argv):
        # stderr bewusst verschlucken, damit die Testausgabe sauber bleibt
        import contextlib
        import io
        with contextlib.redirect_stderr(io.StringIO()) as err:
            code = main(argv)
        self.assertTrue(err.getvalue().strip())
        return code

    def test_conflict_with_own_skill_aborts_without_changes(self):
        eigen = self.ziel / ".agents/skills/alpha"
        eigen.mkdir(parents=True)
        (eigen / "SKILL.md").write_text("mein alpha\n")
        davor = schnappschuss(self.ziel)
        code = self._fehler(["v1.0.0", "--quelle", self.quelle, "--ziel", str(self.ziel)])
        self.assertEqual(code, 2)
        self.assertEqual(schnappschuss(self.ziel), davor)

    def test_unknown_version_aborts_without_changes(self):
        davor = schnappschuss(self.ziel)
        code = self._fehler(["v9.9.9", "--quelle", self.quelle, "--ziel", str(self.ziel)])
        self.assertEqual(code, 2)
        self.assertEqual(schnappschuss(self.ziel), davor)

    def test_pruefen_reports_newer_version(self):
        import contextlib
        import io
        aktualisieren(self.ziel, self.quelle, "v1.0.0")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(pruefen(self.ziel, self.quelle), 1)
            aktualisieren(self.ziel, self.quelle, "v1.10.0")
            self.assertEqual(pruefen(self.ziel, self.quelle), 0)

    def test_repo_copy_matches_stand(self):
        stand = json.loads((REPO / "tools/superpowers/stand.json").read_text())
        self.assertEqual(stand["version"], "v7.0.2")
        self.assertEqual(stand["commit"], "22f0b463e7a5e579904dd6211a520321035526f7")  # Commit hinter dem annotierten Tag (Tag-Objekt: c62ffea)
        self.assertEqual(len(stand["skills"]), 15)
        for name in stand["skills"]:
            self.assertTrue((REPO / ".agents/skills" / name / "SKILL.md").is_file(), name)
        self.assertTrue((REPO / "tools/superpowers/LICENSE").is_file())


if __name__ == "__main__":
    unittest.main()
