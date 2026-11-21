"""Tests für die Anleitung und das README."""

import re
import unittest

from tests.hilfen import REPO


class DokuTest(unittest.TestCase):
    def test_relative_links_resolve(self):
        for datei in ["README.md", "docs/genai-rahmen.md"]:
            pfad = REPO / datei
            text = pfad.read_text(encoding="utf-8")
            for ziel in re.findall(r"\[[^\]]*\]\(([^)\s]+)\)", text):
                if ziel.startswith(("http", "#", "mailto")):
                    continue
                datei_ziel = ziel.split("#", 1)[0]
                self.assertTrue((pfad.parent / datei_ziel).exists(), f"{datei}: {ziel}")

    def test_guide_has_sections(self):
        text = (REPO / "docs/genai-rahmen.md").read_text(encoding="utf-8")
        for h in ["## Was liegt wo", "## Regeln", "## Private Ordner anlegen",
                  "## Prüfen, ob alles erkannt wird", "## Bestehendes im Monorepo übernehmen",
                  "## Später Claude Code dazunehmen", "## Superpowers aktualisieren"]:
            self.assertIn(h, text)

    def test_guide_has_mkdir_for_private_folders(self):
        text = (REPO / "docs/genai-rahmen.md").read_text(encoding="utf-8")
        self.assertIn("mkdir -p ~/.copilot/instructions ~/.copilot/agents ~/.copilot/hooks ~/.agents/skills", text)

    def test_readme_checklist_names_demo_items(self):
        text = (REPO / "README.md").read_text(encoding="utf-8")
        for name in ["commit-nachricht", "privat-beispiel", "reviewer", "azure-devops",
                     "mcp.dev.azure.com/gmhgruppe", "projekte/beispiel-app/AGENTS.md", "docs/genai-rahmen.md",
                     "tools/superpowers/aktualisieren.py --pruefen", "/brainstorming"]:
            self.assertIn(name, text)

    def test_readme_has_no_claude_code_section(self):
        text = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("claude plugin list", text)
