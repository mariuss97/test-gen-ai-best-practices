#!/usr/bin/env python3
"""Copies skills from external sources (e.g. Superpowers, MIT) into the repo.

The sources are maintained by hand in `tools/external-skills/sources.json`. The
skills land flat in `.github/skills/`, separate from the team's own skills in
`.agents/skills/`. Version and commit per source are recorded in
`tools/external-skills/lock.json` (written by the script only), the licenses in
`tools/external-skills/licenses/<source>/LICENSE`. An update is deliberately
manual: run the script, review with `git status` and `git diff --stat`, commit.

Optional keys per source in `sources.json`: `path` (default `skills`),
`license` (default `LICENSE`), `only` (take only these skills) and `exclude`
(do not take these skills). `only` and `exclude` cannot be combined.

The copied files are never edited by hand, only renewed with this script.

Usage: python3 tools/external-skills/update.py [SOURCE [VERSION]]
                                               [--check] [--target PATH]
Without SOURCE all sources are processed. The URL always comes from
`sources.json`. Exit codes: 0 = done or up to date, 1 = newer version
available (only with --check), 2 = error.

On errors before writing, everything stays unchanged. Writing goes through a
staging folder next to the target; if the swap fails, it is rolled back. If
that fails too, the error message says honestly that the repo may be partially
changed and names the way back (`git restore`).
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

SOURCES = "tools/external-skills/sources.json"   # maintained by hand
LOCK = "tools/external-skills/lock.json"         # written by the script only
LICENSES = "tools/external-skills/licenses"      # <source>/LICENSE
SKILLS = ".github/skills"   # external skills (only this script writes here)
OWN = ".agents/skills"      # the team's own skills (never touched)
NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
WAY_BACK = ("The repo may be partially changed. To go back, use "
            "`git restore -- .github/skills tools/external-skills`; check "
            "`git status` for new untracked folders.")


def _move(src, dst):
    os.rename(src, dst)


def _check_names(names, where):
    for n in names:
        if not isinstance(n, str) or not NAME.fullmatch(n):
            raise ValueError(f"Invalid skill name in {where}: {n!r} "
                             "(allowed: lowercase letters, digits, hyphens).")


def _swap(target: Path, clone: Path, source: dict, name: str, old, new, lock_text):
    """Prepare the new copy in staging, then swap; roll back on failure."""
    skills = target / SKILLS
    skills.mkdir(parents=True, exist_ok=True)
    license_target = target / LICENSES / name / "LICENSE"
    staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=skills.parent))
    done = []  # undo list: (from, to)

    def move(src, dst):
        _move(src, dst)
        done.append((src, dst))

    try:
        try:
            for skill in new:
                shutil.copytree(clone / source["path"] / skill, staging / "new" / skill)
            shutil.copy2(clone / source["license"], staging / "LICENSE")
            (staging / "lock.json").write_text(lock_text, encoding="utf-8")
            (staging / "old").mkdir()
            license_target.parent.mkdir(parents=True, exist_ok=True)
            (target / LOCK).parent.mkdir(parents=True, exist_ok=True)
            for skill in old:
                if (skills / skill).exists():
                    move(skills / skill, staging / "old" / skill)
            for skill in new:
                move(staging / "new" / skill, skills / skill)
            for file, path in (("LICENSE", license_target), ("lock.json", target / LOCK)):
                if path.exists():
                    move(path, staging / "old" / ("file-" + file))
                move(staging / file, path)
        except BaseException as error:
            failed = []
            for src, dst in reversed(done):
                try:
                    _move(dst, src)
                except OSError as e:
                    failed.append(f"{dst}: {e}")
            if failed:
                raise OSError(f"{error}. Rollback incomplete. {WAY_BACK}") from error
            raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def _git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True,
                          text=True).stdout.strip()


def _version_number(tag):
    """`v1.10.0` -> (1, 10, 0); anything else -> None."""
    if not tag.startswith("v"):
        return None
    parts = tag[1:].split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        return None
    return tuple(int(p) for p in parts)


def latest_version(url: str) -> str:
    output = _git("ls-remote", "--tags", "--refs", url, "v*")
    tags = []
    for line in output.splitlines():
        tag = line.split("\t")[-1].removeprefix("refs/tags/")
        number = _version_number(tag)
        if number is not None:
            tags.append((number, tag))
    if not tags:
        raise ValueError(f"No version tags (vX.Y.Z) found in {url}.")
    return max(tags)[1]


def _load_json(path: Path, what: str) -> dict:
    if not path.is_file():
        raise ValueError(f"{what} is missing: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as error:
        raise ValueError(f"{what} is not valid JSON: {error}") from error
    if not isinstance(data, dict):
        raise ValueError(f"{what} must be a JSON object.")
    return data


def _old_lock(target: Path) -> dict:
    path = target / LOCK
    return _load_json(path, LOCK) if path.is_file() else {}


def _list(value, key, name):
    if not isinstance(value, list):
        raise ValueError(f"`{key}` of source {name} must be a list.")
    _check_names(value, f"`{key}` of source {name}")
    return value


def _source(target: Path, name: str) -> dict:
    """Entry from sources.json, validated and completed with defaults."""
    if not isinstance(name, str) or not NAME.fullmatch(name):
        raise ValueError(f"Invalid source name: {name!r} "
                         "(allowed: lowercase letters, digits, hyphens).")
    sources = _load_json(target / SOURCES, SOURCES)
    if name not in sources:
        raise ValueError(f"Source {name!r} is not in {SOURCES} "
                         f"(available: {', '.join(sorted(sources)) or 'none'}).")
    raw = sources[name]
    if not isinstance(raw, dict) or not isinstance(raw.get("url"), str) or not raw["url"]:
        raise ValueError(f"Source {name} in {SOURCES} needs a `url`.")
    entry = {"url": raw["url"], "path": raw.get("path", "skills"),
             "license": raw.get("license", "LICENSE")}
    for key in ("path", "license"):
        path = Path(str(entry[key]))
        if not isinstance(entry[key], str) or not entry[key] \
                or path.is_absolute() or ".." in path.parts:
            raise ValueError(f"`{key}` of source {name} must be a relative path "
                             "inside the source.")
    if "only" in raw and "exclude" in raw:
        raise ValueError(f"Source {name}: `only` and `exclude` cannot be combined.")
    for key in ("only", "exclude"):
        if key in raw:
            entry[key] = _list(raw[key], key, name)
    return entry


def update(target: Path, name: str, version: str | None = None) -> dict:
    target = Path(target)
    source = _source(target, name)
    url = source["url"]
    if version is None:
        version = latest_version(url)
    with tempfile.TemporaryDirectory() as tmp:
        clone = Path(tmp) / "clone"
        try:
            _git("clone", "--quiet", "--depth", "1", "--branch", version, url, str(clone))
        except subprocess.CalledProcessError as error:
            raise ValueError(
                f"Version {version} from {url} could not be fetched: {error.stderr.strip()}"
            ) from error
        commit = _git("-C", str(clone), "rev-parse", "HEAD")
        if not (clone / source["path"]).is_dir():
            raise ValueError(f"Folder {source['path']} not found in {name} {version}.")
        if not (clone / source["license"]).is_file():
            raise ValueError(f"License file {source['license']} not found in {name} {version}.")
        available = sorted(p.parent.name for p in (clone / source["path"]).glob("*/SKILL.md"))
        _check_names(available, f"{name} {version}/{source['path']}")
        for key in ("only", "exclude"):
            missing = [n for n in source.get(key, []) if n not in available]
            if missing:
                raise ValueError(f"`{key}` of source {name} names skills that do not exist "
                                 f"in {version}: {', '.join(missing)}")
        new = [n for n in available
               if ("only" not in source or n in source["only"]) and n not in source.get("exclude", [])]
        if not new:
            raise ValueError(f"No skills to take from {name} {version}.")

        lock = _old_lock(target)
        old = lock.get(name, {}).get("skills", [])
        _check_names(old, f"{LOCK} ({name})")

        # Check everything first ...
        own = [n for n in new if (target / OWN / n).exists()]
        if own:
            raise ValueError(
                f"Own skills with the same name exist in {OWN}, aborting: "
                + ", ".join(own)
            )
        for other, entry in lock.items():
            if other == name:
                continue
            duplicates = [n for n in new if n in entry.get("skills", [])]
            if duplicates:
                raise ValueError(
                    f"Skills {', '.join(duplicates)} exist in both sources {other} and {name}, "
                    f"aborting. Exclude them in {SOURCES} for {name} with `exclude`.")
        unknown = [n for n in new if (target / SKILLS / n).exists() and n not in old]
        if unknown:
            raise ValueError(
                f"Folders in {SKILLS} that do not belong to {name}, aborting: "
                + ", ".join(unknown)
            )

        # ... then write (staging, swap, rollback).
        entry = {"url": url, "version": version, "commit": commit, "skills": new}
        new_lock = {**lock, name: entry}
        lock_text = json.dumps(dict(sorted(new_lock.items())), indent=2,
                               ensure_ascii=False) + "\n"
        _swap(target, clone, source, name, old, new, lock_text)
    return entry


def _all_names(target: Path) -> list[str]:
    return sorted(_load_json(target / SOURCES, SOURCES))


def check(target: Path, name: str | None = None) -> int:
    target = Path(target)
    names = _all_names(target) if name is None else [name]
    lock = _old_lock(target)
    code = 0
    for n in names:
        source = _source(target, n)
        installed = lock.get(n, {}).get("version")
        latest = latest_version(source["url"])
        if installed is not None and _version_number(installed) is not None \
                and _version_number(installed) >= _version_number(latest):
            print(f"{n}: up to date ({installed})")
        else:
            print(f"{n}: newer version available: {latest} "
                  f"(installed: {installed or 'none'})")
            code = 1
    return code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Copy skills from external sources into the repo.")
    parser.add_argument("source", nargs="?",
                        help="name from sources.json (default: all sources)")
    parser.add_argument("version", nargs="?",
                        help="tag, e.g. v7.0.2 (default: latest; only with SOURCE)")
    parser.add_argument("--check", action="store_true",
                        help="only check whether a newer version exists")
    parser.add_argument("--target", type=Path, default=Path(__file__).resolve().parents[2],
                        help="root folder of the repo")
    args = parser.parse_args(argv)
    done = []
    try:
        if args.check:
            return check(args.target, args.source)
        names = [args.source] if args.source else _all_names(args.target)
        for name in names:
            entry = update(args.target, name, args.version)
            done.append(name)
            print(f"{name} {entry['version']} copied ({len(entry['skills'])} skills). "
                  "Review with `git status` and `git diff --stat`.")
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        message = getattr(error, "stderr", None) or error
        print(f"Error: {str(message).strip()}", file=sys.stderr)
        if done and len(names) > 1:
            print(f"Already updated: {', '.join(done)}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
