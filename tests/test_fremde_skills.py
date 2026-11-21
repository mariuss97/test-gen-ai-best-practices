"""Tests für das Update-Skript für fremde Skills (offline, mit Fixture-Repo)."""

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from tests.hilfen import REPO

_SPEC = importlib.util.spec_from_file_location(
    "aktualisieren", REPO / "tools/fremde-skills/aktualisieren.py"
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


STAND = "tools/fremde-skills/stand.json"
QUELLEN = "tools/fremde-skills/quellen.json"


def _repo_mit_skills(pfad, skills, lizenz="MIT\n"):
    pfad.mkdir(parents=True)
    for s in skills:
        (pfad / "skills" / s).mkdir(parents=True)
        (pfad / "skills" / s / "SKILL.md").write_text(s + "\n")
    (pfad / "LICENSE").write_text(lizenz)
    git(pfad, "init", "--quiet")
    git(pfad, "add", ".")
    git(pfad, "commit", "--quiet", "-m", "eins")
    git(pfad, "tag", "v1.0.0")
    return git(pfad, "rev-parse", "HEAD")


def _ruhig(funktion, *args):
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return funktion(*args)


class FremdeSkillsTest(unittest.TestCase):
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

        # zweite Quelle: "alpha" gleicht dem Skill der ersten, "delta" ist neu
        self.zweite = tmp / "zweite"
        self.sha_zweite = _repo_mit_skills(self.zweite, ["alpha", "delta"], "Apache\n")

        self.ziel = tmp / "ziel"
        eigen = self.ziel / ".agents/skills/commit-nachricht"
        eigen.mkdir(parents=True)
        self.eigener_skill_text = "eigener skill\n"
        (eigen / "SKILL.md").write_text(self.eigener_skill_text)
        self.schreibe_quellen({"erste": {"url": self.quelle}})

    def schreibe_quellen(self, quellen):
        pfad = self.ziel / QUELLEN
        pfad.parent.mkdir(parents=True, exist_ok=True)
        pfad.write_text(json.dumps(quellen, indent=2) + "\n")

    def zwei_quellen(self, **extra):
        zweite = {"url": self.zweite.as_uri(), **extra}
        self.schreibe_quellen({"erste": {"url": self.quelle}, "zweite": zweite})

    def stand(self):
        return json.loads((self.ziel / STAND).read_text())

    def test_neueste_version_sorts_numerically(self):
        self.assertEqual(neueste_version(self.quelle), "v1.10.0")

    def test_install_copies_skills_and_writes_stand(self):
        eintrag = aktualisieren(self.ziel, "erste", "v1.0.0")
        erwartet = {"url": self.quelle, "version": "v1.0.0",
                    "commit": self.sha_v1_0_0, "skills": ["alpha", "beta"]}
        self.assertEqual(eintrag, erwartet)
        self.assertEqual(self.stand(), {"erste": erwartet})
        self.assertTrue((self.ziel / ".github/skills/alpha/SKILL.md").is_file())
        self.assertEqual(
            (self.ziel / "tools/fremde-skills/lizenzen/erste/LICENSE").read_text(), "MIT\n")
        self.assertEqual(
            (self.ziel / ".agents/skills/commit-nachricht/SKILL.md").read_text(),
            self.eigener_skill_text)

    def test_stand_file_format(self):
        self.zwei_quellen(auslassen=["alpha"])
        aktualisieren(self.ziel, "zweite", "v1.0.0")
        aktualisieren(self.ziel, "erste", "v1.0.0")
        text = (self.ziel / STAND).read_text(encoding="utf-8")
        self.assertTrue(text.endswith("}\n"))
        self.assertEqual(list(json.loads(text)), ["erste", "zweite"])
        self.assertEqual(text, json.dumps(json.loads(text), indent=2, ensure_ascii=False) + "\n")

    def test_executable_bits_preserved(self):
        aktualisieren(self.ziel, "erste", "v1.0.0")
        self.assertTrue(os.access(self.ziel / ".github/skills/beta/scripts/run.sh", os.X_OK))

    def test_update_removes_dropped_skills(self):
        aktualisieren(self.ziel, "erste", "v1.0.0")
        aktualisieren(self.ziel, "erste", "v1.10.0")
        skills = self.ziel / ".github/skills"
        eigene = self.ziel / ".agents/skills"
        self.assertTrue((skills / "alpha/SKILL.md").is_file())
        self.assertTrue((skills / "gamma/SKILL.md").is_file())
        self.assertFalse((skills / "beta").exists())
        self.assertFalse((skills / "commit-nachricht").exists())
        self.assertEqual((eigene / "commit-nachricht/SKILL.md").read_text(),
                         self.eigener_skill_text)
        self.assertEqual(self.stand()["erste"]["skills"], ["alpha", "gamma"])

    def test_same_version_twice_is_idempotent(self):
        aktualisieren(self.ziel, "erste", "v1.0.0")
        davor = schnappschuss(self.ziel)
        aktualisieren(self.ziel, "erste", "v1.0.0")
        self.assertEqual(schnappschuss(self.ziel), davor)

    def _fehler(self, argv):
        # stderr bewusst verschlucken, damit die Testausgabe sauber bleibt
        import contextlib
        import io
        with contextlib.redirect_stderr(io.StringIO()) as err:
            code = main(argv)
        self.assertTrue(err.getvalue().strip())
        return code

    def _fehler_ohne_aenderung(self, *argv):
        davor = schnappschuss(self.ziel)
        code = self._fehler([*argv, "--ziel", str(self.ziel)])
        self.assertEqual(code, 2)
        self.assertEqual(schnappschuss(self.ziel), davor)

    def test_conflict_with_own_skill_aborts_without_changes(self):
        eigen = self.ziel / ".agents/skills/alpha"
        eigen.mkdir(parents=True)
        (eigen / "SKILL.md").write_text("mein alpha\n")
        self._fehler_ohne_aenderung("erste", "v1.0.0")

    def test_unknown_folder_in_external_skills_aborts_without_changes(self):
        fremd = self.ziel / ".github/skills/alpha"
        fremd.mkdir(parents=True)
        (fremd / "SKILL.md").write_text("unbekanntes alpha\n")
        self._fehler_ohne_aenderung("erste", "v1.0.0")

    def test_external_skills_stay_out_of_own_folder(self):
        aktualisieren(self.ziel, "erste", "v1.0.0")
        eigene = sorted(p.name for p in (self.ziel / ".agents/skills").iterdir())
        self.assertEqual(eigene, ["commit-nachricht"])

    def test_name_clash_between_sources_aborts_and_names_both(self):
        self.zwei_quellen()
        aktualisieren(self.ziel, "erste", "v1.0.0")
        davor = schnappschuss(self.ziel)
        import contextlib
        import io
        with contextlib.redirect_stderr(io.StringIO()) as err:
            code = main(["zweite", "v1.0.0", "--ziel", str(self.ziel)])
        self.assertEqual(code, 2)
        for wort in ("erste", "zweite", "alpha", "auslassen"):
            self.assertIn(wort, err.getvalue())
        self.assertEqual(schnappschuss(self.ziel), davor)

    def test_auslassen_resolves_name_clash(self):
        self.zwei_quellen(auslassen=["alpha"])
        aktualisieren(self.ziel, "erste", "v1.0.0")
        eintrag = aktualisieren(self.ziel, "zweite", "v1.0.0")
        self.assertEqual(eintrag["skills"], ["delta"])
        self.assertEqual((self.ziel / ".github/skills/alpha/SKILL.md").read_text(), "alpha\n")
        self.assertTrue((self.ziel / ".github/skills/delta/SKILL.md").is_file())

    def test_nur_copies_only_named_skills(self):
        self.zwei_quellen(nur=["delta"])
        eintrag = aktualisieren(self.ziel, "zweite", "v1.0.0")
        self.assertEqual(eintrag["skills"], ["delta"])
        self.assertFalse((self.ziel / ".github/skills/alpha").exists())

    def test_nur_and_auslassen_together_abort(self):
        self.zwei_quellen(nur=["delta"], auslassen=["alpha"])
        self._fehler_ohne_aenderung("zweite", "v1.0.0")

    def test_unknown_name_in_nur_or_auslassen_aborts(self):
        for schluessel in ("nur", "auslassen"):
            with self.subTest(schluessel=schluessel):
                self.zwei_quellen(**{schluessel: ["deltaa"]})
                self._fehler_ohne_aenderung("zweite", "v1.0.0")

    def test_invalid_name_in_nur_aborts(self):
        self.zwei_quellen(nur=["../x"])
        self._fehler_ohne_aenderung("zweite", "v1.0.0")

    def test_custom_pfad_and_lizenz(self):
        pfad = self.zweite.parent / "dritte"
        (pfad / "agent/skills/eins").mkdir(parents=True)
        (pfad / "agent/skills/eins/SKILL.md").write_text("eins\n")
        (pfad / "doku").mkdir()
        (pfad / "doku/COPYING").write_text("GPL\n")
        git(pfad, "init", "--quiet")
        git(pfad, "add", ".")
        git(pfad, "commit", "--quiet", "-m", "x")
        git(pfad, "tag", "v1.0.0")
        self.schreibe_quellen({"dritte": {"url": pfad.as_uri(), "pfad": "agent/skills",
                                          "lizenz": "doku/COPYING"}})
        aktualisieren(self.ziel, "dritte", "v1.0.0")
        self.assertEqual(
            (self.ziel / "tools/fremde-skills/lizenzen/dritte/LICENSE").read_text(), "GPL\n")
        self.assertTrue((self.ziel / ".github/skills/eins/SKILL.md").is_file())

    def test_missing_pfad_or_lizenz_aborts(self):
        self.schreibe_quellen({"erste": {"url": self.quelle, "pfad": "nirgends"}})
        self._fehler_ohne_aenderung("erste", "v1.0.0")
        self.schreibe_quellen({"erste": {"url": self.quelle, "lizenz": "NIRGENDS"}})
        self._fehler_ohne_aenderung("erste", "v1.0.0")

    def test_pfad_must_stay_inside_source(self):
        self.schreibe_quellen({"erste": {"url": self.quelle, "pfad": "../.."}})
        self._fehler_ohne_aenderung("erste", "v1.0.0")

    def test_second_source_update_leaves_first_untouched(self):
        self.zwei_quellen(auslassen=["alpha"])
        aktualisieren(self.ziel, "erste", "v1.0.0")
        erste_skills = schnappschuss(self.ziel / ".github/skills")
        erster_eintrag = self.stand()["erste"]
        aktualisieren(self.ziel, "zweite", "v1.0.0")
        self.assertEqual(self.stand()["erste"], erster_eintrag)
        self.assertEqual(self.stand()["zweite"]["commit"], self.sha_zweite)
        nachher = schnappschuss(self.ziel / ".github/skills")
        for pfad, inhalt in erste_skills.items():
            self.assertEqual(nachher[pfad], inhalt)

    def test_readme_in_skills_folder_is_left_alone(self):
        readme = self.ziel / ".github/skills/README.md"
        readme.parent.mkdir(parents=True)
        readme.write_text("hinweis\n")
        aktualisieren(self.ziel, "erste", "v1.0.0")
        aktualisieren(self.ziel, "erste", "v1.10.0")
        self.assertEqual(readme.read_text(), "hinweis\n")

    def _stand_mit(self, skills):
        pfad = self.ziel / STAND
        pfad.parent.mkdir(parents=True, exist_ok=True)
        pfad.write_text(json.dumps({"erste": {"version": "v0.0.1", "skills": skills}}))

    def test_invalid_old_skill_names_abort_without_changes(self):
        for name in ["../..", ""]:
            with self.subTest(name=name):
                self._stand_mit([name])
                self._fehler_ohne_aenderung("erste", "v1.0.0")

    def _fehler_im_tausch(self, ab_aufruf, nur_einmal):
        aktualisieren(self.ziel, "erste", "v1.0.0")
        davor = schnappschuss(self.ziel)
        echt = _MODUL._verschieben
        zaehler = {"n": 0}

        def kaputt(von, nach):
            zaehler["n"] += 1
            if zaehler["n"] == ab_aufruf or (not nur_einmal and zaehler["n"] > ab_aufruf):
                raise OSError("simulierter Fehler")
            echt(von, nach)

        import contextlib
        import io
        with mock.patch.object(_MODUL, "_verschieben", kaputt), \
                contextlib.redirect_stderr(io.StringIO()) as err:
            code = main(["erste", "v1.10.0", "--ziel", str(self.ziel)])
        return code, davor, err.getvalue()

    def _kein_staging(self):
        reste = [p.name for p in (self.ziel / ".github").iterdir() if p.name.startswith(".staging")]
        self.assertEqual(reste, [])

    def test_write_failure_rolls_back_and_leaves_no_staging(self):
        code, davor, _ = self._fehler_im_tausch(ab_aufruf=5, nur_einmal=True)
        self.assertEqual(code, 2)
        self.assertEqual(schnappschuss(self.ziel), davor)
        self._kein_staging()

    def test_failed_rollback_message_names_git_restore(self):
        code, _, meldung = self._fehler_im_tausch(ab_aufruf=5, nur_einmal=False)
        self.assertEqual(code, 2)
        self.assertIn("git restore -- .github/skills tools/fremde-skills", meldung)
        self._kein_staging()

    def test_unknown_version_aborts_without_changes(self):
        self._fehler_ohne_aenderung("erste", "v9.9.9")

    def test_unknown_source_name_aborts_without_changes(self):
        self._fehler_ohne_aenderung("gibtsnicht", "v1.0.0")
        self._fehler_ohne_aenderung("../x")

    def test_missing_or_broken_quellen_json_aborts(self):
        (self.ziel / QUELLEN).write_text("{kaputt")
        self._fehler_ohne_aenderung("erste")
        (self.ziel / QUELLEN).unlink()
        self._fehler_ohne_aenderung("erste")

    def test_pruefen_per_source(self):
        import contextlib
        import io
        aktualisieren(self.ziel, "erste", "v1.0.0")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(pruefen(self.ziel, "erste"), 1)
            self.assertIn("erste: neuere Version verfügbar: v1.10.0 (installiert: v1.0.0)",
                          out.getvalue())
            aktualisieren(self.ziel, "erste", "v1.10.0")
            self.assertEqual(pruefen(self.ziel, "erste"), 0)
            self.assertIn("erste: aktuell (v1.10.0)", out.getvalue())

    def test_pruefen_all_sources(self):
        import contextlib
        import io
        self.zwei_quellen(auslassen=["alpha"])
        aktualisieren(self.ziel, "erste", "v1.10.0")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(pruefen(self.ziel), 1)
            self.assertIn("erste: aktuell (v1.10.0)", out.getvalue())
            self.assertIn("zweite: neuere Version verfügbar: v1.0.0 (installiert: keine)",
                          out.getvalue())
            aktualisieren(self.ziel, "zweite", "v1.0.0")
            self.assertEqual(pruefen(self.ziel), 0)

    def test_main_without_source_updates_all(self):
        self.zwei_quellen(auslassen=["alpha"])
        self.assertEqual(_ruhig(main, ["--ziel", str(self.ziel)]), 0)
        self.assertEqual(sorted(self.stand()), ["erste", "zweite"])
        self.assertEqual(self.stand()["erste"]["version"], "v1.10.0")

    def test_main_all_reports_already_updated_on_failure(self):
        # zweite Quelle kollidiert mit der ersten -> Fehler nach erfolgreicher erster
        self.zwei_quellen()
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()) as err:
            code = main(["--ziel", str(self.ziel)])
        self.assertEqual(code, 2)
        self.assertIn("Schon aktualisiert: erste", err.getvalue())
        self.assertEqual(list(self.stand()), ["erste"])

    def test_main_pruefen_exit_codes(self):
        aktualisieren(self.ziel, "erste", "v1.0.0")
        self.assertEqual(_ruhig(main, ["--pruefen", "--ziel", str(self.ziel)]), 1)
        aktualisieren(self.ziel, "erste", "v1.10.0")
        self.assertEqual(_ruhig(main, ["--pruefen", "--ziel", str(self.ziel)]), 0)

    def test_repo_copy_matches_stand(self):
        stand = json.loads((REPO / STAND).read_text())
        eintrag = stand["superpowers"]
        self.assertEqual(eintrag["version"], "v7.0.2")
        self.assertEqual(eintrag["commit"], "22f0b463e7a5e579904dd6211a520321035526f7")  # Commit hinter dem annotierten Tag (Tag-Objekt: c62ffea)
        self.assertEqual(len(eintrag["skills"]), 15)
        for name in eintrag["skills"]:
            self.assertTrue((REPO / ".github/skills" / name / "SKILL.md").is_file(), name)
        self.assertTrue((REPO / "tools/fremde-skills/lizenzen/superpowers/LICENSE").is_file())
        self.assertFalse((REPO / "tools/superpowers").exists())
        quellen = json.loads((REPO / QUELLEN).read_text())
        self.assertEqual(quellen["superpowers"]["url"], eintrag["url"])


if __name__ == "__main__":
    unittest.main()
