"""Red agent: a tool-calling attacker that can only reach sandbox targets."""
import json
import re

from arena.discover import find_login_path, normalize_route, routes as discover_routes
from arena.httptool import HostLockError, send_request
from arena.llm import BudgetExceeded
from arena.payloads import get_payload_templates
from arena.referee import Exploit, find_flags, find_token

OBSERVATION_CHARS = 800
KEEP_STEPS = 6

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
    return [f"{r.method} {r.path}" for r in discover_routes(openapi)]


def _prelogin(base_url: str, openapi: dict, users: list, emit, login_path=None) -> dict | None:
    """Log in once before the model speaks, so no step or token is spent on /api/login."""
    if not users:
        return None
    path = find_login_path(openapi, login_path)
    if not path:
        return None
    body = {"username": users[0]["username"], "password": users[0]["password"]}
    try:
        res = send_request("POST", base_url + path, json=body)
    except Exception as exc:
        emit({"type": "red_error", "tool": "prelogin", "error": str(exc)})
        return None
    emit({"type": "red_action", "tool": "prelogin", "source": "setup", "status": res.status,
          "args": {"method": "POST", "path": path}})
    token = find_token(res.body) if res.status == 200 else None
    return {"path": path, "json": body, "token": token} if token else None


def run_red(llm, base_url: str, openapi: dict, users: list, emit, max_steps: int = 25,
            flag_owners: dict | None = None, login: dict | None = None,
            login_path: str | None = None, keep_steps: int = KEEP_STEPS) -> list[Exploit]:
    accounts = ", ".join(f"{u['username']}/{u['password']}" for u in users if u.get("role") != "admin")
    login = login if login and login.get("token") else _prelogin(base_url, openapi, users, emit,
                                                                login_path)
    intro = f"Test accounts (normal users): {accounts}."
    if login:
        intro += (f" You are already logged in as {login['json']['username']}; send the header "
                  f'"Authorization": "Bearer {login["token"]}" with requests that need it.')
    preamble = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": intro + " Begin."}]
    history: list[list[dict]] = []
    found: dict[str, Exploit] = {}
    logins: dict[str, dict] = {}
    if login:
        logins[login["token"]] = {"path": login["path"], "json": login["json"]}
    owners = flag_owners or {}
    for _ in range(max_steps):
        messages = list(preamble)
        for group in history[-keep_steps:]:
            messages.extend(group)
        try:
            reply = llm.chat(messages, TOOLS)
        except BudgetExceeded:
            raise  # let the orchestrator end the match with a clear reason
        except RuntimeError as exc:  # provider down: keep what we already found
            emit({"type": "red_error", "tool": "chat", "error": str(exc)})
            break
        calls = reply.get("tool_calls") or []
        if not calls:
            break
        group = [{"role": "assistant", "content": reply.get("content"), "tool_calls": [
            {"id": c["id"], "type": "function",
             "function": {"name": c["name"], "arguments": c["arguments"]}} for c in calls]}]
        for call in calls:
            result = _run_tool(call, base_url, openapi, emit, found, logins, owners)
            group.append({"role": "tool", "tool_call_id": call["id"], "content": result})
        history.append(group)
    return list(found.values())


def _run_tool(call, base_url, openapi, emit, found, logins, owners) -> str:
    name = call["name"]
    try:
        args = json.loads(call["arguments"] or "{}")
    except json.JSONDecodeError as exc:
        emit({"type": "red_error", "tool": name, "error": f"bad arguments: {exc}"})
        return f"error: arguments were not valid JSON ({exc})"
    if not isinstance(args, dict):
        emit({"type": "red_error", "tool": name, "error": "arguments must be a JSON object"})
        return "error: arguments must be a JSON object"
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
    body_json = args.get("json") or {}
    if res.status == 200 and isinstance(body_json, dict) and "password" in body_json:
        token = find_token(res.body)
        if token:
            logins[token] = {"path": path, "json": body_json}
    flags = find_flags(res.body)
    for flag in flags:
        if flag not in found:
            login = None
            for value in (args.get("headers") or {}).values():
                login = logins.get(str(value).split(" ")[-1]) or login
            owner = owners.get(flag)
            if owner and login and owner == login["json"].get("username"):
                continue  # the owner reading their own data is not a breach
            ex = Exploit(args.get("method", "GET"), path, args.get("headers"), args.get("params"),
                         args.get("json"), flag, classify(path, args.get("params")), login)
            found[flag] = ex
            emit({"type": "breach", "source": "llm", "route": normalize_route(path),
                  "vuln_class": ex.vuln_class, "flag": flag, "method": ex.method, "path": path,
                  **({"params": ex.params} if ex.params else {}),
                  **({"json": ex.json} if ex.json else {})})
    note = f"\nFLAGS FOUND: {', '.join(flags)}" if flags else ""
    return f"status {res.status}\n{res.body[:OBSERVATION_CHARS]}{note}"
