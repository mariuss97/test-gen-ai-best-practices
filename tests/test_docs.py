"""Tests for the guide and the README."""

import re
import unittest

from tests.helpers import REPO


class DocsTest(unittest.TestCase):
    def test_relative_links_resolve(self):
        for file in ["README.md", "docs/genai-framework.md"]:
            path = REPO / file
            text = path.read_text(encoding="utf-8")
            for link in re.findall(r"\[[^\]]*\]\(([^)\s]+)\)", text):
                if link.startswith(("http", "#", "mailto")):
                    continue
                file_target = link.split("#", 1)[0]
                self.assertTrue((path.parent / file_target).exists(), f"{file}: {link}")

    def test_guide_has_sections(self):
        text = (REPO / "docs/genai-framework.md").read_text(encoding="utf-8")
        for heading in ["## Was liegt wo", "## Regeln", "## Private Ordner anlegen",
                        "## Prüfen, ob alles erkannt wird", "## Bestehendes im Monorepo übernehmen",
                        "## Später Claude Code dazunehmen", "## Fremde Skills aktualisieren"]:
            self.assertIn(heading, text)

    def test_guide_has_mkdir_for_private_folders(self):
        text = (REPO / "docs/genai-framework.md").read_text(encoding="utf-8")
        self.assertIn("mkdir -p ~/.copilot/instructions ~/.copilot/agents ~/.copilot/hooks ~/.agents/skills", text)

    def test_readme_checklist_names_demo_items(self):
        text = (REPO / "README.md").read_text(encoding="utf-8")
        for name in ["commit-message", "private-example", "reviewer", "azure-devops",
                     "mcp.dev.azure.com/gmhgruppe", "projects/example-app/AGENTS.md", "docs/genai-framework.md",
                     "tools/external-skills/update.py --check", "/brainstorming"]:
            self.assertIn(name, text)

    def test_readme_has_no_claude_code_section(self):
        text = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("claude plugin list", text)
