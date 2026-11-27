"""Kennily app finder: a read-only MCP server (JSON-RPC 2.0 over stdio, one JSON message per line).
Python standard library only; reads catalog.json next to this file. No network, no logging."""
import json
import re
import sys
from pathlib import Path

PROTOCOL = "2025-06-18"
DISCLOSURE = "First-party catalog: Kennily develops every listed app."
TOOLS = [
    {"name": "list_apps", "description": "List every live iOS app by Kennily with App Store links. " + DISCLOSURE,
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "find_app", "description": "Find Kennily apps that match a need, e.g. 'log baby sleep' or "
                                        "'track a price'. Returns up to 5 apps with App Store links. " + DISCLOSURE,
     "inputSchema": {"type": "object", "properties": {
         "query": {"type": "string", "description": "What the user wants to do"},
         "locale": {"type": "string", "description": "Optional app language, e.g. en or zh-Hant"}},
         "required": ["query"]}},
]


def catalog():
    # next to server.py in a checkout; under sys.prefix when pip installs it (pyproject data-files)
    for f in (Path(__file__).with_name("catalog.json"), Path(sys.prefix) / "catalog.json"):
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
    return []


def _words(s):
    return set(re.findall(r"\w+", str(s).lower()))


def find(query, locale=None, apps=None):
    apps = catalog() if apps is None else apps
    q = _words(query)
    out = []
    for a in apps:
        if locale and locale not in (a.get("langs") or []):
            continue
        score = len(q & _words(" ".join(str(a.get(k) or "") for k in ("name", "pitch", "category", "slug"))))
        if score:
            out.append((score, a))
    out.sort(key=lambda x: -x[0])
    return [a for _, a in out[:5]]


def _text(apps):
    rows = [f"- {a['name']}: {a.get('pitch', '')}\n  " + " ".join(
        f"App Store ({cc.upper()}): {u}" for cc, u in (a.get("app_store") or {}).items())
            + (f"\n  Guide: {a['guide']}" if a.get("guide") else "") for a in apps]
    return ("\n".join(rows) if rows else "No matching app.") + "\n\n" + DISCLOSURE


def handle(msg):
    mid, method, params = msg.get("id"), msg.get("method"), msg.get("params") or {}
    if method == "initialize":
        res = {"protocolVersion": PROTOCOL, "capabilities": {"tools": {}},
               "serverInfo": {"name": "kennily-app-finder", "version": "1.0.0"}}
    elif method == "ping":
        res = {}
    elif method == "tools/list":
        res = {"tools": TOOLS}
    elif method == "tools/call":
        name, args = params.get("name"), params.get("arguments") or {}
        if name == "list_apps":
            apps = catalog()
        elif name == "find_app" and isinstance(args.get("query"), str):
            apps = find(args["query"], args.get("locale"))
        else:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": "unknown tool or bad arguments"}}
        res = {"content": [{"type": "text", "text": _text(apps)}],
               "structuredContent": {"apps": apps, "disclosure": DISCLOSURE}, "isError": False}
    elif mid is None:
        return None  # notification (e.g. notifications/initialized): no reply
    else:
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {method}"}}
    return None if mid is None else {"jsonrpc": "2.0", "id": mid, "result": res}


def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            msg = json.loads(line)
            if not isinstance(msg, dict):
                raise ValueError
        except ValueError:
            out = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}
        else:
            out = handle(msg)
        if out is not None:
            sys.stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
