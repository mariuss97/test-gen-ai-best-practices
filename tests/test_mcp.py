"""Tests für die geteilte MCP-Konfiguration (.mcp.json)."""

import json
import unittest

from tests.hilfen import REPO


class TestMcpKonfiguration(unittest.TestCase):

    def test_mcp_json_registers_azure_devops_remote_server(self):
        konfig = json.loads((REPO / ".mcp.json").read_text(encoding="utf-8"))
        self.assertEqual(konfig, {
            "mcpServers": {
                "azure-devops": {
                    "type": "http",
                    "url": "https://mcp.dev.azure.com/gmhgruppe",
                }
            }
        })

    def test_no_local_mcp_servers_need_a_runtime(self):
        # Geteilte Server sollen ohne Laufzeit pro Nutzer (z. B. nvm) starten.
        konfig = json.loads((REPO / ".mcp.json").read_text(encoding="utf-8"))
        for name, eintrag in konfig["mcpServers"].items():
            self.assertNotIn("command", eintrag, name)

    def test_demo_server_is_gone(self):
        self.assertFalse((REPO / "tools/mcp-demo").exists())


if __name__ == "__main__":
    unittest.main()
