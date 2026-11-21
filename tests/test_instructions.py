"""Tests für AGENTS.md, Projekt-Anweisungen und Markdown-Regeln."""

import unittest

from tests.hilfen import REPO, frontmatter


class AnweisungenTest(unittest.TestCase):
    def test_agents_md_exists_and_points_to_guide(self):
        text = (REPO / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("docs/genai-rahmen.md", text)
        self.assertIn("using-superpowers", text)

    def test_project_agents_md_has_marker(self):
        text = (REPO / "projekte/beispiel-app/AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Regeln aus projekte/beispiel-app/AGENTS.md aktiv.", text)

    def test_markdown_instructions_apply_to_md(self):
        fm = frontmatter(REPO / ".github/instructions/markdown.instructions.md")
        self.assertEqual(fm["applyTo"], "**/*.md")
        self.assertTrue(fm["description"])


if __name__ == "__main__":
    unittest.main()
