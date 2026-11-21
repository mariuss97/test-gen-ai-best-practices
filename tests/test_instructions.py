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

    def test_spring_boot_instructions_apply_to_java(self):
        fm = frontmatter(REPO / ".github/instructions/java-spring-boot.instructions.md")
        self.assertEqual(fm["applyTo"], "**/*.java")
        self.assertTrue(fm["description"])

    def test_spring_boot_instructions_name_the_target_stack(self):
        text = (REPO / ".github/instructions/java-spring-boot.instructions.md").read_text(encoding="utf-8")
        for fact in ["Spring Boot 4.1.1", "Java 21", "21.0.9", "tools.jackson", "@MockitoBean",
                     "spring-boot-starter-webmvc", "org.jspecify.annotations.Nullable"]:
            self.assertIn(fact, text)
        self.assertNotIn("JUnit 5", text)

    def test_spring_boot_instructions_use_gradle_only(self):
        text = (REPO / ".github/instructions/java-spring-boot.instructions.md").read_text(encoding="utf-8")
        self.assertIn("Gradle 9.7.1", text)
        self.assertIn("./gradlew build", text)
        for maven in ["mvnw", "Maven", "pom.xml"]:
            self.assertNotIn(maven, text)

    def test_spring_boot_instructions_credit_their_source(self):
        text = (REPO / ".github/instructions/java-spring-boot.instructions.md").read_text(encoding="utf-8")
        self.assertIn("https://github.com/github/awesome-copilot", text)
        self.assertIn("docs/third-party-licenses/awesome-copilot-LICENSE", text)
        license_text = (REPO / "docs/third-party-licenses/awesome-copilot-LICENSE").read_text(encoding="utf-8")
        self.assertIn("Copyright GitHub, Inc.", license_text)


if __name__ == "__main__":
    unittest.main()
