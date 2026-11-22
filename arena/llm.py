"""Thin OpenAI-compatible chat wrapper. Provider is chosen only by environment variables."""
import os
from pathlib import Path

from openai import OpenAI


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


class LLM:
    def __init__(self, role: str):
        load_env()
        self.model = (os.environ.get(f"ARENA_{role.upper()}_MODEL")
                      or os.environ.get("ARENA_MODEL") or "gpt-4o-mini")
        self._client = OpenAI(base_url=os.environ.get("ARENA_BASE_URL") or None,
                              api_key=os.environ.get("ARENA_API_KEY", "missing"))
        self.tokens_used = 0

    def chat(self, messages: list, tools: list | None = None) -> dict:
        kwargs = {"model": self.model, "messages": messages}
        if tools:
            kwargs["tools"] = tools
        resp = self._client.chat.completions.create(**kwargs)
        if resp.usage:
            self.tokens_used += resp.usage.total_tokens or 0
        msg = resp.choices[0].message
        calls = [{"id": c.id, "name": c.function.name, "arguments": c.function.arguments}
                 for c in (msg.tool_calls or [])]
        return {"content": msg.content, "tool_calls": calls}
