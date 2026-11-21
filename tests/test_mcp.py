"""Tests for the shared MCP configuration (.mcp.json, if present)."""

import json
import unittest

from tests.helpers import REPO


class McpConfigTest(unittest.TestCase):

    def test_no_local_mcp_servers_need_a_runtime(self):
        # Shared servers must start without a per-user runtime (e.g. nvm).
        path = REPO / ".mcp.json"
        if not path.exists():
            self.skipTest("no .mcp.json in the repo")
        config = json.loads(path.read_text(encoding="utf-8"))
        for name, entry in config["mcpServers"].items():
            self.assertNotIn("command", entry, name)


if __name__ == "__main__":
    unittest.main()
