"""Shared helpers for the tests."""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def frontmatter(path):
    """Reads the key/value lines between the first and second `---`."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    data = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        data[key.strip()] = value
    return data


def jsonc(path):
    """Reads JSON and ignores lines starting with `//` (also indented)."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return json.loads("\n".join(l for l in lines if not l.lstrip().startswith("//")))
