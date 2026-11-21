"""Tests für den Demo-MCP-Server (tools/mcp-demo/server.py) und .mcp.json."""

import json
import os
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GRUSS = "Hallo aus dem GenAI-Rahmen: Der MCP-Server aus .mcp.json läuft auf dem Linux-Rechner."


def run_server(lines, env=None):
    """Startet den Server, schickt die Zeilen und gibt die Antworten als JSON zurück."""
    eingabe = "".join(zeile + "\n" for zeile in lines)
    proc = subprocess.run(
        ["python3", "tools/mcp-demo/server.py"],
        cwd=REPO,
        input=eingabe.encode("utf-8"),
        capture_output=True,
        timeout=5,
        env=env,
    )
    return [json.loads(z) for z in proc.stdout.decode("utf-8").splitlines() if z.strip()]


def anfrage(id_, method, params=None):
    nachricht = {"jsonrpc": "2.0", "id": id_, "method": method}
    if params is not None:
        nachricht["params"] = params
    return json.dumps(nachricht)


class McpDemoTest(unittest.TestCase):
    def test_initialize_echoes_client_version(self):
        [r] = run_server([json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}})])
        self.assertEqual(r["id"], 1)
        self.assertEqual(r["result"]["protocolVersion"], "2025-11-25")
        self.assertIn("tools", r["result"]["capabilities"])
        self.assertEqual(r["result"]["serverInfo"]["name"], "genai-demo")

    def test_initialize_without_version_uses_default(self):
        [r] = run_server([anfrage(1, "initialize", {"capabilities": {}})])
        self.assertEqual(r["result"]["protocolVersion"], "2025-06-18")

    def test_notification_gets_no_response(self):
        antworten = run_server([
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
            anfrage(7, "ping"),
        ])
        self.assertEqual(len(antworten), 1)
        self.assertEqual(antworten[0]["id"], 7)
        self.assertEqual(antworten[0]["result"], {})

    def test_tools_list_contains_demo_gruss(self):
        [r] = run_server([anfrage(2, "tools/list")])
        tools = r["result"]["tools"]
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["name"], "demo_gruss")
        self.assertTrue(tools[0]["description"])
        self.assertEqual(tools[0]["inputSchema"], {"type": "object", "properties": {}})

    def test_tools_call_returns_gruss_under_lang_c(self):
        env = {k: v for k, v in os.environ.items() if k != "PYTHONIOENCODING"}
        env["LANG"] = "C"
        env["LC_ALL"] = "C"
        [r] = run_server([anfrage(3, "tools/call", {"name": "demo_gruss", "arguments": {}})], env=env)
        self.assertEqual(r["result"]["content"], [{"type": "text", "text": GRUSS}])
        self.assertIs(r["result"]["isError"], False)

    def test_unknown_tool_is_error(self):
        [r] = run_server([anfrage(4, "tools/call", {"name": "gibt_es_nicht", "arguments": {}})])
        self.assertEqual(r["error"]["code"], -32602)

    def test_unknown_method_is_error(self):
        [r] = run_server([anfrage(5, "foo/bar")])
        self.assertEqual(r["error"]["code"], -32601)

    def test_blank_and_broken_lines_keep_server_alive(self):
        erste, zweite = run_server(["", "{kaputt", anfrage(3, "ping")])
        self.assertEqual(erste["error"]["code"], -32700)
        self.assertIsNone(erste["id"])
        self.assertEqual(zweite["id"], 3)

    def test_mcp_json_points_to_server(self):
        konfig = json.loads((REPO / ".mcp.json").read_text(encoding="utf-8"))
        eintrag = konfig["mcpServers"]["genai-demo"]
        self.assertEqual(eintrag["command"], "python3")
        self.assertEqual(eintrag["args"], ["tools/mcp-demo/server.py"])
        self.assertTrue((REPO / eintrag["args"][0]).is_file())


if __name__ == "__main__":
    unittest.main()
