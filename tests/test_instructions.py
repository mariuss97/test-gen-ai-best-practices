"""Tests for AGENTS.md, project instructions and Markdown rules."""

import unittest

from tests.helpers import REPO, frontmatter


class InstructionsTest(unittest.TestCase):
    def test_agents_md_exists_and_points_to_guide(self):
        text = (REPO / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("docs/genai-framework.md", text)
        self.assertIn("using-superpowers", text)

    def test_project_agents_md_has_marker(self):
        text = (REPO / "projects/example-app/AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Rules from projects/example-app/AGENTS.md active.", text)

    def test_markdown_instructions_apply_to_md(self):
        fm = frontmatter(REPO / ".github/instructions/markdown.instructions.md")
        self.assertEqual(fm["applyTo"], "**/*.md")
        self.assertTrue(fm["description"])


if __name__ == "__main__":
    unittest.main()
