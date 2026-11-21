#!/usr/bin/env python3
"""Minimaler MCP-Server (stdio) für die GenAI-Rahmen-Demo.

Er zeigt, dass ein Server aus `.mcp.json` im Workspace startet und ein Werkzeug
(`demo_gruss`) bereitstellt. Er dient nur zur Demo und nutzt ausschließlich die
Python-Standardbibliothek.

Protokoll: JSON-RPC 2.0, eine Nachricht pro Zeile auf stdin, eine Antwort pro
Zeile auf stdout. Auf stdout wird sonst nichts geschrieben.
"""

import json
import sys

SERVER_NAME = "genai-demo"
TOOL_NAME = "demo_gruss"
GRUSS = "Hallo aus dem GenAI-Rahmen: Der MCP-Server aus .mcp.json läuft auf dem Linux-Rechner."
DEFAULT_PROTOCOL_VERSION = "2025-06-18"

TOOL = {
    "name": TOOL_NAME,
    "description": "Gibt einen festen Gruß zurück, um zu zeigen, dass der MCP-Server läuft.",
    "inputSchema": {"type": "object", "properties": {}},
}


def _result(id_, result):
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _error(id_, code, message):
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


def handle(message):
    """Beantwortet eine JSON-RPC-Nachricht. Gibt None zurück, wenn keine Antwort nötig ist."""
    if "id" not in message:
        return None
    id_ = message["id"]
    method = message.get("method")
    params = message.get("params") or {}

    if method == "initialize":
        return _result(id_, {
            "protocolVersion": params.get("protocolVersion", DEFAULT_PROTOCOL_VERSION),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": "1.0.0"},
        })
    if method == "ping":
        return _result(id_, {})
    if method == "tools/list":
        return _result(id_, {"tools": [TOOL]})
    if method == "tools/call":
        if params.get("name") != TOOL_NAME:
            return _error(id_, -32602, f"Unbekanntes Werkzeug: {params.get('name')}")
        return _result(id_, {"content": [{"type": "text", "text": GRUSS}], "isError": False})
    return _error(id_, -32601, f"Unbekannte Methode: {method}")


def _send(antwort):
    # ensure_ascii (Standard) hält die Ausgabe unabhängig vom Locale.
    sys.stdout.write(json.dumps(antwort) + "\n")
    sys.stdout.flush()


def main():
    for zeile in sys.stdin:
        if not zeile.strip():
            continue
        try:
            message = json.loads(zeile)
        except json.JSONDecodeError:
            _send(_error(None, -32700, "Ungültiges JSON"))
            continue
        if not isinstance(message, dict):
            _send(_error(None, -32600, "Ungültige Anfrage"))
            continue
        antwort = handle(message)
        if antwort is not None:
            _send(antwort)


if __name__ == "__main__":
    main()
