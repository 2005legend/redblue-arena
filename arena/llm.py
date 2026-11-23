"""OpenAI-compatible chat wrapper with per-role model routing and automatic fallback.

Model choice, highest priority first:
  1. ARENA_<ROLE>_MODEL in the environment pins ONE model (bypasses routing).
  2. models.yaml (or ARENA_MODELS_FILE): an ordered candidate list per role.
  3. ARENA_MODEL, then a built-in default.
If a model errors (rate limit, timeout, bad gateway) or returns an empty reply, the next candidate
is tried and the failed one rests for `cooldown` seconds.

Set ARENA_TOKEN_BUDGET (or token_budget=) to stop an agent once it has spent that many tokens.
Each LLM instance (one per role) counts its own budget. 0 means unlimited.
"""
import os
import time
from pathlib import Path

import yaml
from openai import OpenAI


class BudgetExceeded(RuntimeError):
    """A run has spent its token budget; stop before calling the provider again."""


def load_env(path=".env") -> None:
    """Load KEY=VALUE lines from a .env file. Real environment variables win; empty values are ignored."""
    p = Path(path)
    if not p.is_file():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip().strip('"').strip("'")
        if value:
            os.environ.setdefault(key.strip(), value)


def load_routes(path) -> dict:
    p = Path(path)
    if not p.is_file():
        return {}
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return {role: list(models) for role, models in (data.get("roles") or {}).items()}


class OpenAIClient:
    """One chat call against the configured provider. Returns (message_dict, tokens_used)."""

    def __init__(self):
        self._c = OpenAI(base_url=os.environ.get("ARENA_BASE_URL") or None,
                         api_key=os.environ.get("ARENA_API_KEY", "missing"),
                         timeout=90, max_retries=1)

    def complete(self, model, messages, tools):
        kwargs = {"model": model, "messages": messages}
        if tools:
            kwargs["tools"] = tools
        resp = self._c.chat.completions.create(**kwargs)
        msg = resp.choices[0].message
        calls = [{"id": c.id, "name": c.function.name, "arguments": c.function.arguments}
                 for c in (msg.tool_calls or [])]
        used = (resp.usage.total_tokens or 0) if resp.usage else 0
        return {"content": msg.content, "tool_calls": calls}, used


class LLM:
    def __init__(self, role: str, models: list | None = None, client=None, cooldown: float = 60,
                 token_budget: int | None = None):
        load_env()
        self.role, self.cooldown = role, cooldown
        self.models = models or self._resolve(role)
        self._client = client or OpenAIClient()
        self.token_budget = (token_budget if token_budget is not None
                             else int(os.environ.get("ARENA_TOKEN_BUDGET") or 0))
        self._rest_until: dict[str, float] = {}
        self.tokens_used = 0
        self.calls = 0
        self.tokens_by_model: dict[str, int] = {}
        self.last_model: str | None = None
        self.failures: list[str] = []

    @staticmethod
    def _resolve(role: str) -> list:
        pinned = os.environ.get(f"ARENA_{role.upper()}_MODEL")
        if pinned:
            return [pinned]
        routed = load_routes(os.environ.get("ARENA_MODELS_FILE", "models.yaml")).get(role)
        if routed:
            return routed
        return [os.environ.get("ARENA_MODEL") or "gpt-4o-mini"]

    def chat(self, messages: list, tools: list | None = None) -> dict:
        if self.token_budget and self.tokens_used >= self.token_budget:
            raise BudgetExceeded(
                f"token budget {self.token_budget} exhausted ({self.tokens_used} tokens used)")
        now = time.time()
        ready = [m for m in self.models if self._rest_until.get(m, 0) <= now] or self.models
        errors = []
        for model in ready:
            try:
                msg, used = self._client.complete(model, messages, tools)
                if not msg.get("content") and not msg.get("tool_calls"):
                    raise RuntimeError("empty reply")
            except Exception as exc:  # any provider failure: rest this model and try the next
                self._rest_until[model] = time.time() + self.cooldown
                errors.append(f"{model}: {str(exc)[:160]}")
                self.failures.append(errors[-1])
                continue
            self.last_model = model
            self.calls += 1
            self.tokens_used += used
            self.tokens_by_model[model] = self.tokens_by_model.get(model, 0) + used
            return msg
        raise RuntimeError("all models failed: " + " | ".join(errors))
