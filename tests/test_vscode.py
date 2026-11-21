"""Tests für die geteilten VS-Code-Dateien und die .gitignore."""

import subprocess
import unittest

from tests.hilfen import REPO, jsonc


class VSCodeTest(unittest.TestCase):
    def test_settings_enable_nested_agents_md_only(self):
        self.assertEqual(jsonc(REPO / ".vscode/settings.json"), {"chat.useNestedAgentsMdFiles": True})

    def test_settings_explain_why(self):
        self.assertIn("//", (REPO / ".vscode/settings.json").read_text(encoding="utf-8"))

    def test_extensions_recommend_copilot_chat(self):
        self.assertEqual(jsonc(REPO / ".vscode/extensions.json")["recommendations"], ["github.copilot-chat"])

    def test_gitignore_entries(self):
        lines = (REPO / ".gitignore").read_text(encoding="utf-8").splitlines()
        for entry in ["CLAUDE.md", "CLAUDE.local.md", ".claude/", ".superpowers/"]:
            self.assertIn(entry, lines)

    def test_claude_files_ignored_and_untracked(self):
        # git check-ignore -q akzeptiert nur einen Pfad, daher je Pfad einzeln prüfen.
        for pfad in ["CLAUDE.md", ".claude/settings.json"]:
            r = subprocess.run(["git", "check-ignore", "-q", pfad], cwd=REPO)
            self.assertEqual(r.returncode, 0, pfad)
        tracked = subprocess.run(
            ["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True
        ).stdout.splitlines()
        self.assertFalse([p for p in tracked if p == "CLAUDE.md" or p.startswith(".claude/")])
