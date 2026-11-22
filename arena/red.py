"""Red agent: a tool-calling attacker that can only reach sandbox targets."""
import json
import re

from arena.httptool import HostLockError, send_request
from arena.payloads import get_payload_templates
from arena.referee import Exploit, find_flags

SYSTEM = (
    "You are the Red agent in a local security exercise. You are attacking a small web API that "
    "its owner runs in an isolated sandbox on this machine, with permission. Your goal is to "
    "find hidden canary strings that look like FLAG{...}. Work step by step: call discover_routes, "
    "log in with the test accounts you are given, then try SQL injection, IDOR (other users' "
    "ids) and calling admin routes as a normal user. Use get_payload_templates for ideas. "
    "Stop when you have tried every route or run out of ideas."
)

TOOLS = [
    {"type": "function", "function": {
        "name": "discover_routes", "description": "List the API's routes from its OpenAPI spec.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "send_http_request",
        "description": "Send one HTTP request to the target app (path is relative).",
        "parameters": {"type": "object", "properties": {
            "method": {"type": "string"}, "path": {"type": "string"},
            "headers": {"type": "object"}, "params": {"type": "object"},
            "json": {"type": "object"}}, "required": ["method", "path"]}}},
    {"type": "function", "function": {
        "name": "get_payload_templates",
        "description": "Get payload ideas for a vulnerability class: sqli, idor, admin_bypass, path_traversal.",
        "parameters": {"type": "object", "properties": {"vuln_class": {"type": "string"}},
                       "required": ["vuln_class"]}}},
]


def normalize_route(path: str) -> str:
    return re.sub(r"/\d+", "/{id}", path.split("?")[0])


def classify(path: str, params: dict | None) -> str:
    text = path + " " + json.dumps(params or {})
    if "admin" in path:
        return "admin_bypass"
    if ".." in text:
        return "path_traversal"
    if re.search(r"'|--|\bOR\b|UNION", text, re.I):
        return "sqli"
    if re.search(r"/\d+", path):
        return "idor"
    return "unknown"


def _routes(openapi: dict) -> list[str]:
    return [f"{m.upper()} {p}" for p, ms in openapi.get("paths", {}).items() for m in ms]


def run_red(llm, base_url: str, openapi: dict, users: list, emit, max_steps: int = 25) -> list[Exploit]:
    accounts = ", ".join(f"{u['username']}/{u['password']}" for u in users if u.get("role") != "admin")
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"Test accounts (normal users): {accounts}. Begin."}]
    found: dict[str, Exploit] = {}
    for _ in range(max_steps):
        reply = llm.chat(messages, TOOLS)
        calls = reply.get("tool_calls") or []
        if not calls:
            break
        messages.append({"role": "assistant", "content": reply.get("content"), "tool_calls": [
            {"id": c["id"], "type": "function",
             "function": {"name": c["name"], "arguments": c["arguments"]}} for c in calls]})
        for call in calls:
            result = _run_tool(call, base_url, openapi, emit, found)
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": result})
    return list(found.values())


def _run_tool(call, base_url, openapi, emit, found) -> str:
    name = call["name"]
    try:
        args = json.loads(call["arguments"] or "{}")
    except json.JSONDecodeError as exc:
        emit({"type": "red_error", "tool": name, "error": f"bad arguments: {exc}"})
        return f"error: arguments were not valid JSON ({exc})"
    if name == "discover_routes":
        emit({"type": "red_action", "tool": name, "args": {}, "status": None})
        return json.dumps(_routes(openapi))
    if name == "get_payload_templates":
        emit({"type": "red_action", "tool": name, "args": args, "status": None})
        return json.dumps(get_payload_templates(args.get("vuln_class", "")))
    if name != "send_http_request":
        return f"error: unknown tool {name}"
    path = args.get("path", "/")
    try:
        res = send_request(args.get("method", "GET"), base_url + path, headers=args.get("headers"),
                           params=args.get("params"), json=args.get("json"))
    except HostLockError as exc:
        emit({"type": "red_error", "tool": name, "error": str(exc)})
        return f"blocked: {exc}"
    except Exception as exc:
        emit({"type": "red_error", "tool": name, "error": str(exc)})
        return f"error: {exc}"
    emit({"type": "red_action", "tool": name, "status": res.status,
          "args": {"method": args.get("method", "GET"), "path": path, "params": args.get("params")}})
    for flag in find_flags(res.body):
        if flag not in found:
            ex = Exploit(args.get("method", "GET"), path, args.get("headers"), args.get("params"),
                         args.get("json"), flag, classify(path, args.get("params")))
            found[flag] = ex
            emit({"type": "breach", "route": normalize_route(path), "vuln_class": ex.vuln_class,
                  "flag": flag, "path": path})
    return f"status {res.status}\n{res.body}"
