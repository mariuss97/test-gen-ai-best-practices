"""Tests for shared skills and the reviewer agent."""

import json
import re
import subprocess
import unittest

from tests.helpers import REPO, frontmatter


class SkillsAgentsTest(unittest.TestCase):
    def test_skill_names_match_folders(self):
        skills = sorted([*(REPO / ".agents/skills").glob("*/SKILL.md"),
                         *(REPO / ".github/skills").glob("*/SKILL.md")])
        self.assertTrue(skills)
        for s in skills:
            fm = frontmatter(s)
            self.assertEqual(fm["name"], s.parent.name)
            self.assertRegex(fm["name"], r"^[a-z0-9]+(-[a-z0-9]+)*$")
            self.assertTrue(fm["description"])

    def test_commit_skill_marks_format_as_example(self):
        text = (REPO / ".agents/skills/commit-message/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("<bereich>: <Beschreibung im Imperativ>", text)
        self.assertIn("Beispiel", text)

    def test_own_and_external_skills_are_separate(self):
        lock = json.loads((REPO / "tools/external-skills/lock.json").read_text(encoding="utf-8"))
        external = [skill for entry in lock.values() for skill in entry["skills"]]
        self.assertEqual(len(external), len(set(external)))
        own = sorted(p.parent.name for p in (REPO / ".agents/skills").glob("*/SKILL.md"))
        in_github = sorted(p.parent.name for p in (REPO / ".github/skills").glob("*/SKILL.md"))
        self.assertEqual(in_github, sorted(external))
        self.assertFalse(set(own) & set(external))
        self.assertIn("update.py", (REPO / ".github/skills/README.md").read_text(encoding="utf-8"))

    def test_reviewer_is_read_only(self):
        fm = frontmatter(REPO / ".github/agents/reviewer.agent.md")
        self.assertTrue(fm["description"])
        tools = set(re.findall(r"[a-z]+", fm["tools"]))
        self.assertEqual(tools, {"read", "search"})

    def test_no_private_files_tracked(self):
        out = subprocess.run(
            ["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True
        ).stdout
        self.assertNotIn("private-", out)


if __name__ == "__main__":
    unittest.main()
