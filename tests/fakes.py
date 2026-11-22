import json


class FakeLLM:
    """Returns scripted assistant messages: dicts with content and tool_calls."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = 0
        self.tokens_used = 0

    def chat(self, messages, tools=None):
        self.calls += 1
        if not self.script:
            return {"content": "done", "tool_calls": []}
        return self.script.pop(0)


def tc(name, args, id="t1", raw=None):
    return {"content": None, "tool_calls": [
        {"id": id, "name": name, "arguments": raw if raw is not None else json.dumps(args)}]}
