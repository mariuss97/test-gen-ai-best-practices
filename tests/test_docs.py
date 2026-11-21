"""Tests for the guide and the README."""

import re
import subprocess
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
        for heading in ["## What goes where", "## Rules", "## Create private folders",
                        "## Private MCP servers", "## Check that everything is detected",
                        "## Take over existing files in the monorepo",
                        "## Adding Claude Code later", "## Updating external skills"]:
            self.assertIn(heading, text)

    def test_guide_documents_private_mcp_config(self):
        text = (REPO / "docs/genai-framework.md").read_text(encoding="utf-8")
        self.assertIn("~/.copilot/mcp-config.json", text)
        self.assertIn('"url": "https://mcp.dev.azure.com/gmhgruppe"', text)

    def test_guide_has_mkdir_for_private_folders(self):
        text = (REPO / "docs/genai-framework.md").read_text(encoding="utf-8")
        self.assertIn("mkdir -p ~/.copilot/instructions ~/.copilot/agents ~/.copilot/hooks ~/.agents/skills", text)

    def test_readme_checklist_names_demo_items(self):
        text = (REPO / "README.md").read_text(encoding="utf-8")
        for name in ["commit-message", "private-example", "reviewer", "azure-devops",
                     "mcp.dev.azure.com/gmhgruppe", "~/.copilot/mcp-config.json", "projects/example-app/AGENTS.md", "docs/genai-framework.md",
                     "tools/external-skills/update.py --check", "/brainstorming"]:
            self.assertIn(name, text)

    def test_readme_has_no_claude_code_section(self):
        text = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("claude plugin list", text)


class LanguageTest(unittest.TestCase):
    def test_no_german_umlauts_in_tracked_text_files(self):
        files = subprocess.run(
            ["git", "ls-files", "*.md", "*.py", "*.json"],
            cwd=REPO, capture_output=True, text=True, check=True,
        ).stdout.splitlines()
        vendored = {p.name for p in (REPO / ".github/skills").iterdir() if p.is_dir()}
        for file in files:
            if file.startswith("docs/superpowers/plans/"):
                continue
            parts = file.split("/")
            if file.startswith(".github/skills/") and len(parts) > 3 and parts[2] in vendored:
                continue
            text = (REPO / file).read_text(encoding="utf-8")
            self.assertIsNone(re.search("[\u00e4\u00f6\u00fc\u00c4\u00d6\u00dc\u00df]", text), file)
