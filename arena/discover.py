"""Read a target's OpenAPI spec into the small route table the sweep and Red share."""
import re
from dataclasses import dataclass, field

HTTP_METHODS = ("get", "post", "put", "patch", "delete")


@dataclass
class Param:
    name: str
    location: str  # "path" or "query"
    type: str = "string"
    required: bool = False


@dataclass
class Route:
    method: str
    path: str
    params: list = field(default_factory=list)

    def path_params(self) -> list:
        return [p for p in self.params if p.location == "path"]

    def query_params(self) -> list:
        return [p for p in self.params if p.location == "query"]


def routes(openapi: dict) -> list[Route]:
    out = []
    for path, methods in (openapi.get("paths") or {}).items():
        shared = methods.get("parameters") or []
        for method in HTTP_METHODS:
            op = methods.get(method)
            if not isinstance(op, dict):
                continue
            params = []
            for raw in shared + (op.get("parameters") or []):
                loc = raw.get("in")
                if loc in ("path", "query"):
                    schema = raw.get("schema") or {}
                    params.append(Param(raw.get("name", ""), loc,
                                        schema.get("type", "string"), bool(raw.get("required"))))
            out.append(Route(method.upper(), path, params))
    return out


def _body_fields(op: dict, openapi: dict) -> set:
    content = (op.get("requestBody") or {}).get("content") or {}
    schema = (content.get("application/json") or {}).get("schema") or {}
    ref = schema.get("$ref", "")
    if ref.startswith("#/components/schemas/"):
        name = ref.rsplit("/", 1)[-1]
        schema = (openapi.get("components") or {}).get("schemas", {}).get(name) or {}
    return set((schema.get("properties") or {}).keys())


def find_login_path(openapi: dict, override: str | None = None) -> str | None:
    """The POST route whose JSON body takes a username and a password."""
    if override:
        return override
    for path, methods in (openapi.get("paths") or {}).items():
        op = methods.get("post")
        if isinstance(op, dict) and {"username", "password"} <= _body_fields(op, openapi):
            return path
    return None


def normalize_route(path: str) -> str:
    return re.sub(r"/\d+", "/{id}", path.split("?")[0])
