"""Tests for the MCP setup: the repo ships no MCP server."""

import unittest

from tests.helpers import REPO


class McpConfigTest(unittest.TestCase):

    def test_repo_ships_no_mcp_config(self):
        # MCP servers are configured privately in ~/.copilot/mcp-config.json
        # (see docs/genai-framework.md, "Private MCP servers"). If the team
        # decides to share a server, replace this test with one that checks
        # the shared .mcp.json (remote servers only, no per-user runtime).
        for path in (".mcp.json", ".vscode/mcp.json"):
            self.assertFalse((REPO / path).exists(), f"{path} must not be in the repo")


if __name__ == "__main__":
    unittest.main()
