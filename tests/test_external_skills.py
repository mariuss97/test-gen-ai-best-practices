"""Tests for the update script for external skills (offline, with fixture repos)."""

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from tests.helpers import REPO

_SPEC = importlib.util.spec_from_file_location(
    "update_script", REPO / "tools/external-skills/update.py"
)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
latest_version = _MODULE.latest_version
update = _MODULE.update
check = _MODULE.check
main = _MODULE.main

GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t",
       "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false"]


def git(cwd, *args):
    return subprocess.run(GIT + list(args), cwd=cwd, check=True,
                          capture_output=True, text=True).stdout.strip()


def snapshot(path):
    """All files under path (relative path -> content)."""
    path = Path(path)
    return {str(p.relative_to(path)): p.read_bytes()
            for p in sorted(path.rglob("*")) if p.is_file()}


LOCK = "tools/external-skills/lock.json"
SOURCES = "tools/external-skills/sources.json"


def _repo_with_skills(path, skills, license="MIT\n"):
    path.mkdir(parents=True)
    for s in skills:
        (path / "skills" / s).mkdir(parents=True)
        (path / "skills" / s / "SKILL.md").write_text(s + "\n")
    (path / "LICENSE").write_text(license)
    git(path, "init", "--quiet")
    git(path, "add", ".")
    git(path, "commit", "--quiet", "-m", "one")
    git(path, "tag", "v1.0.0")
    return git(path, "rev-parse", "HEAD")


def _quiet(funktion, *args):
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return funktion(*args)


class ExternalSkillsTest(unittest.TestCase):
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
        git(up, "commit", "--quiet", "-m", "one")
        self.sha_v1_0_0 = git(up, "rev-parse", "HEAD")
        git(up, "tag", "v1.0.0")
        git(up, "tag", "v1.2.0")
        git(up, "rm", "--quiet", "-r", "skills/beta")
        (up / "skills/gamma").mkdir()
        (up / "skills/gamma/SKILL.md").write_text("gamma\n")
        git(up, "add", ".")
        git(up, "commit", "--quiet", "-m", "two")
        git(up, "tag", "v1.10.0")
        self.source_url = up.as_uri()

        # second source: "alpha" matches the skill of the first, "delta" is new
        self.second = tmp / "second"
        self.sha_second = _repo_with_skills(self.second, ["alpha", "delta"], "Apache\n")

        self.target = tmp / "target"
        eigen = self.target / ".agents/skills/commit-message"
        eigen.mkdir(parents=True)
        self.own_skill_text = "own skill\n"
        (eigen / "SKILL.md").write_text(self.own_skill_text)
        self.write_sources({"first": {"url": self.source_url}})

    def write_sources(self, sources):
        path = self.target / SOURCES
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(sources, indent=2) + "\n")

    def two_sources(self, **extra):
        second = {"url": self.second.as_uri(), **extra}
        self.write_sources({"first": {"url": self.source_url}, "second": second})

    def lock(self):
        return json.loads((self.target / LOCK).read_text())

    def test_latest_version_sorts_numerically(self):
        self.assertEqual(latest_version(self.source_url), "v1.10.0")

    def test_install_copies_skills_and_writes_lock(self):
        entry = update(self.target, "first", "v1.0.0")
        expected = {"url": self.source_url, "version": "v1.0.0",
                    "commit": self.sha_v1_0_0, "skills": ["alpha", "beta"]}
        self.assertEqual(entry, expected)
        self.assertEqual(self.lock(), {"first": expected})
        self.assertTrue((self.target / ".github/skills/alpha/SKILL.md").is_file())
        self.assertEqual(
            (self.target / "tools/external-skills/licenses/first/LICENSE").read_text(), "MIT\n")
        self.assertEqual(
            (self.target / ".agents/skills/commit-message/SKILL.md").read_text(),
            self.own_skill_text)

    def test_lock_file_format(self):
        self.two_sources(exclude=["alpha"])
        update(self.target, "second", "v1.0.0")
        update(self.target, "first", "v1.0.0")
        text = (self.target / LOCK).read_text(encoding="utf-8")
        self.assertTrue(text.endswith("}\n"))
        self.assertEqual(list(json.loads(text)), ["first", "second"])
        self.assertEqual(text, json.dumps(json.loads(text), indent=2, ensure_ascii=False) + "\n")

    def test_executable_bits_preserved(self):
        update(self.target, "first", "v1.0.0")
        self.assertTrue(os.access(self.target / ".github/skills/beta/scripts/run.sh", os.X_OK))

    def test_update_removes_dropped_skills(self):
        update(self.target, "first", "v1.0.0")
        update(self.target, "first", "v1.10.0")
        skills = self.target / ".github/skills"
        own = self.target / ".agents/skills"
        self.assertTrue((skills / "alpha/SKILL.md").is_file())
        self.assertTrue((skills / "gamma/SKILL.md").is_file())
        self.assertFalse((skills / "beta").exists())
        self.assertFalse((skills / "commit-message").exists())
        self.assertEqual((own / "commit-message/SKILL.md").read_text(),
                         self.own_skill_text)
        self.assertEqual(self.lock()["first"]["skills"], ["alpha", "gamma"])

    def test_same_version_twice_is_idempotent(self):
        update(self.target, "first", "v1.0.0")
        before = snapshot(self.target)
        update(self.target, "first", "v1.0.0")
        self.assertEqual(snapshot(self.target), before)

    def _error(self, argv):
        # swallow stderr on purpose to keep the test output clean
        import contextlib
        import io
        with contextlib.redirect_stderr(io.StringIO()) as err:
            code = main(argv)
        self.assertTrue(err.getvalue().strip())
        return code

    def _error_without_change(self, *argv):
        before = snapshot(self.target)
        code = self._error([*argv, "--target", str(self.target)])
        self.assertEqual(code, 2)
        self.assertEqual(snapshot(self.target), before)

    def test_conflict_with_own_skill_aborts_without_changes(self):
        eigen = self.target / ".agents/skills/alpha"
        eigen.mkdir(parents=True)
        (eigen / "SKILL.md").write_text("my alpha\n")
        self._error_without_change("first", "v1.0.0")

    def test_unknown_folder_in_external_skills_aborts_without_changes(self):
        foreign = self.target / ".github/skills/alpha"
        foreign.mkdir(parents=True)
        (foreign / "SKILL.md").write_text("unknown alpha\n")
        self._error_without_change("first", "v1.0.0")

    def test_external_skills_stay_out_of_own_folder(self):
        update(self.target, "first", "v1.0.0")
        own = sorted(p.name for p in (self.target / ".agents/skills").iterdir())
        self.assertEqual(own, ["commit-message"])

    def test_name_clash_between_sources_aborts_and_names_both(self):
        self.two_sources()
        update(self.target, "first", "v1.0.0")
        before = snapshot(self.target)
        import contextlib
        import io
        with contextlib.redirect_stderr(io.StringIO()) as err:
            code = main(["second", "v1.0.0", "--target", str(self.target)])
        self.assertEqual(code, 2)
        for word in ("first", "second", "alpha", "exclude"):
            self.assertIn(word, err.getvalue())
        self.assertEqual(snapshot(self.target), before)

    def test_exclude_resolves_name_clash(self):
        self.two_sources(exclude=["alpha"])
        update(self.target, "first", "v1.0.0")
        entry = update(self.target, "second", "v1.0.0")
        self.assertEqual(entry["skills"], ["delta"])
        self.assertEqual((self.target / ".github/skills/alpha/SKILL.md").read_text(), "alpha\n")
        self.assertTrue((self.target / ".github/skills/delta/SKILL.md").is_file())

    def test_only_copies_only_named_skills(self):
        self.two_sources(only=["delta"])
        entry = update(self.target, "second", "v1.0.0")
        self.assertEqual(entry["skills"], ["delta"])
        self.assertFalse((self.target / ".github/skills/alpha").exists())

    def test_only_and_exclude_together_abort(self):
        self.two_sources(only=["delta"], exclude=["alpha"])
        self._error_without_change("second", "v1.0.0")

    def test_unknown_name_in_only_or_exclude_aborts(self):
        for key in ("only", "exclude"):
            with self.subTest(key=key):
                self.two_sources(**{key: ["deltaa"]})
                self._error_without_change("second", "v1.0.0")

    def test_invalid_name_in_nur_aborts(self):
        self.two_sources(only=["../x"])
        self._error_without_change("second", "v1.0.0")

    def test_custom_path_and_license(self):
        path = self.second.parent / "third"
        (path / "agent/skills/eins").mkdir(parents=True)
        (path / "agent/skills/eins/SKILL.md").write_text("one\n")
        (path / "docs").mkdir()
        (path / "docs/COPYING").write_text("GPL\n")
        git(path, "init", "--quiet")
        git(path, "add", ".")
        git(path, "commit", "--quiet", "-m", "x")
        git(path, "tag", "v1.0.0")
        self.write_sources({"third": {"url": path.as_uri(), "path": "agent/skills",
                                          "license": "docs/COPYING"}})
        update(self.target, "third", "v1.0.0")
        self.assertEqual(
            (self.target / "tools/external-skills/licenses/third/LICENSE").read_text(), "GPL\n")
        self.assertTrue((self.target / ".github/skills/eins/SKILL.md").is_file())

    def test_missing_path_or_license_aborts(self):
        self.write_sources({"first": {"url": self.source_url, "path": "nowhere"}})
        self._error_without_change("first", "v1.0.0")
        self.write_sources({"first": {"url": self.source_url, "license": "NOWHERE"}})
        self._error_without_change("first", "v1.0.0")

    def test_path_must_stay_inside_source(self):
        self.write_sources({"first": {"url": self.source_url, "path": "../.."}})
        self._error_without_change("first", "v1.0.0")

    def test_second_source_update_leaves_first_untouched(self):
        self.two_sources(exclude=["alpha"])
        update(self.target, "first", "v1.0.0")
        first_skills = snapshot(self.target / ".github/skills")
        first_entry = self.lock()["first"]
        update(self.target, "second", "v1.0.0")
        self.assertEqual(self.lock()["first"], first_entry)
        self.assertEqual(self.lock()["second"]["commit"], self.sha_second)
        after = snapshot(self.target / ".github/skills")
        for path, content in first_skills.items():
            self.assertEqual(after[path], content)

    def test_readme_in_skills_folder_is_left_alone(self):
        readme = self.target / ".github/skills/README.md"
        readme.parent.mkdir(parents=True)
        readme.write_text("note\n")
        update(self.target, "first", "v1.0.0")
        update(self.target, "first", "v1.10.0")
        self.assertEqual(readme.read_text(), "note\n")

    def _lock_with(self, skills):
        path = self.target / LOCK
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"first": {"version": "v0.0.1", "skills": skills}}))

    def test_invalid_old_skill_names_abort_without_changes(self):
        for name in ["../..", ""]:
            with self.subTest(name=name):
                self._lock_with([name])
                self._error_without_change("first", "v1.0.0")

    def _error_during_swap(self, from_call, only_once):
        update(self.target, "first", "v1.0.0")
        before = snapshot(self.target)
        real = _MODULE._move
        counter = {"n": 0}

        def broken(von, nach):
            counter["n"] += 1
            if counter["n"] == from_call or (not only_once and counter["n"] > from_call):
                raise OSError("simulated error")
            real(von, nach)

        import contextlib
        import io
        with mock.patch.object(_MODULE, "_move", broken), \
                contextlib.redirect_stderr(io.StringIO()) as err:
            code = main(["first", "v1.10.0", "--target", str(self.target)])
        return code, before, err.getvalue()

    def _no_staging(self):
        leftovers = [p.name for p in (self.target / ".github").iterdir() if p.name.startswith(".staging")]
        self.assertEqual(leftovers, [])

    def test_write_failure_rolls_back_and_leaves_no_staging(self):
        code, before, _ = self._error_during_swap(from_call=5, only_once=True)
        self.assertEqual(code, 2)
        self.assertEqual(snapshot(self.target), before)
        self._no_staging()

    def test_failed_rollback_message_names_git_restore(self):
        code, _, message = self._error_during_swap(from_call=5, only_once=False)
        self.assertEqual(code, 2)
        self.assertIn("git restore -- .github/skills tools/external-skills", message)
        self._no_staging()

    def test_unknown_version_aborts_without_changes(self):
        self._error_without_change("first", "v9.9.9")

    def test_unknown_source_name_aborts_without_changes(self):
        self._error_without_change("doesnotexist", "v1.0.0")
        self._error_without_change("../x")

    def test_missing_or_broken_sources_json_aborts(self):
        (self.target / SOURCES).write_text("{broken")
        self._error_without_change("first")
        (self.target / SOURCES).unlink()
        self._error_without_change("first")

    def test_check_per_source(self):
        import contextlib
        import io
        update(self.target, "first", "v1.0.0")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(check(self.target, "first"), 1)
            self.assertIn("first: newer version available: v1.10.0 (installed: v1.0.0)",
                          out.getvalue())
            update(self.target, "first", "v1.10.0")
            self.assertEqual(check(self.target, "first"), 0)
            self.assertIn("first: up to date (v1.10.0)", out.getvalue())

    def test_check_all_sources(self):
        import contextlib
        import io
        self.two_sources(exclude=["alpha"])
        update(self.target, "first", "v1.10.0")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(check(self.target), 1)
            self.assertIn("first: up to date (v1.10.0)", out.getvalue())
            self.assertIn("second: newer version available: v1.0.0 (installed: none)",
                          out.getvalue())
            update(self.target, "second", "v1.0.0")
            self.assertEqual(check(self.target), 0)

    def test_main_without_source_updates_all(self):
        self.two_sources(exclude=["alpha"])
        self.assertEqual(_quiet(main, ["--target", str(self.target)]), 0)
        self.assertEqual(sorted(self.lock()), ["first", "second"])
        self.assertEqual(self.lock()["first"]["version"], "v1.10.0")

    def test_main_all_reports_already_updated_on_failure(self):
        # second source clashes with the first -> error after the first succeeded
        self.two_sources()
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()) as err:
            code = main(["--target", str(self.target)])
        self.assertEqual(code, 2)
        self.assertIn("Already updated: first", err.getvalue())
        self.assertEqual(list(self.lock()), ["first"])

    def test_main_check_exit_codes(self):
        update(self.target, "first", "v1.0.0")
        self.assertEqual(_quiet(main, ["--check", "--target", str(self.target)]), 1)
        update(self.target, "first", "v1.10.0")
        self.assertEqual(_quiet(main, ["--check", "--target", str(self.target)]), 0)

    def test_repo_copy_matches_lock(self):
        lock = json.loads((REPO / LOCK).read_text())
        entry = lock["superpowers"]
        self.assertEqual(entry["version"], "v7.0.2")
        self.assertEqual(entry["commit"], "22f0b463e7a5e579904dd6211a520321035526f7")  # commit behind the annotated tag (tag object: c62ffea)
        self.assertEqual(len(entry["skills"]), 15)
        for name in entry["skills"]:
            self.assertTrue((REPO / ".github/skills" / name / "SKILL.md").is_file(), name)
        self.assertTrue((REPO / "tools/external-skills/licenses/superpowers/LICENSE").is_file())
        self.assertFalse((REPO / "tools/superpowers").exists())
        sources = json.loads((REPO / SOURCES).read_text())
        self.assertEqual(sources["superpowers"]["url"], entry["url"])


if __name__ == "__main__":
    unittest.main()
