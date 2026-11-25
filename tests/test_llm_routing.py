import pytest

from arena.llm import LLM, load_routes

OK = {"content": "hi", "tool_calls": []}


class FakeClient:
    """Stands in for the provider client: behaviour per model id is scripted."""

    def __init__(self, behaviour):
        self.behaviour, self.calls = behaviour, []

    def complete(self, model, messages, tools):
        self.calls.append(model)
        b = self.behaviour[model]
        if isinstance(b, Exception):
            raise b
        return b, 10


def make(models, behaviour, **kw):
    c = FakeClient(behaviour)
    return LLM("red", models=models, client=c, **kw), c


def test_falls_back_when_first_model_raises():
    llm, c = make(["a", "b"], {"a": RuntimeError("429 rate limit"), "b": OK})
    assert llm.chat([{"role": "user", "content": "x"}]) == OK
    assert c.calls == ["a", "b"] and llm.last_model == "b"


def test_empty_reply_counts_as_failure():
    llm, c = make(["a", "b"], {"a": {"content": None, "tool_calls": []}, "b": OK})
    assert llm.chat([]) == OK and c.calls == ["a", "b"]


def test_failed_model_cools_down_then_is_skipped():
    llm, c = make(["a", "b"], {"a": RuntimeError("boom"), "b": OK}, cooldown=60)
    llm.chat([])
    llm.chat([])
    assert c.calls == ["a", "b", "b"]


def test_all_models_failing_raises_with_every_error():
    llm, _ = make(["a", "b"], {"a": RuntimeError("one"), "b": RuntimeError("two")})
    with pytest.raises(RuntimeError) as e:
        llm.chat([])
    assert "one" in str(e.value) and "two" in str(e.value)


def test_tokens_counted_per_model():
    llm, _ = make(["a"], {"a": OK})
    llm.chat([])
    llm.chat([])
    assert llm.tokens_used == 20 and llm.tokens_by_model == {"a": 20}


def test_load_routes_and_env_pin(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # keep the project .env out of this test
    f = tmp_path / "models.yaml"
    f.write_text("roles:\n  red: [x, y]\n  blue: [z]\n")
    assert load_routes(f) == {"red": ["x", "y"], "blue": ["z"]}
    monkeypatch.setenv("ARENA_MODELS_FILE", str(f))
    monkeypatch.delenv("ARENA_RED_MODEL", raising=False)
    assert LLM("red", client=FakeClient({})).models == ["x", "y"]
    monkeypatch.setenv("ARENA_RED_MODEL", "pinned")
    assert LLM("red", client=FakeClient({})).models == ["pinned"]


def test_token_budget_stops_a_runaway_loop():
    from arena.llm import BudgetExceeded
    llm, c = make(["a"], {"a": OK}, token_budget=25)
    llm.chat([]); llm.chat([]); llm.chat([])  # 30 tokens used
    with pytest.raises(BudgetExceeded):
        llm.chat([])
    assert len(c.calls) == 3  # the fourth call never reached the provider


def test_no_budget_means_unlimited():
    llm, _ = make(["a"], {"a": OK}, token_budget=0)
    for _ in range(5):
        llm.chat([])
    assert llm.tokens_used == 50


def test_cooldown_is_configurable_and_can_be_disabled(monkeypatch):
    monkeypatch.delenv("ARENA_MODEL_COOLDOWN", raising=False)
    assert LLM("red", models=["a"], client=FakeClient({"a": OK})).cooldown == 60
    monkeypatch.setenv("ARENA_MODEL_COOLDOWN", "0")
    assert LLM("red", models=["a"], client=FakeClient({"a": OK})).cooldown == 0


def test_provider_settings_come_from_env_then_model_file(tmp_path, monkeypatch):
    from arena.llm import resolve_provider
    for k in ("ARENA_BASE_URL", "ARENA_API_KEY", "FREELLMAPI_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    f = tmp_path / "models.yaml"
    f.write_text("base_url: http://h:3001/v1\napi_key_env: FREELLMAPI_API_KEY\nroles:\n  red: [x]\n")
    monkeypatch.setenv("FREELLMAPI_API_KEY", "file-key")
    assert resolve_provider(f) == ("http://h:3001/v1", "file-key")
    monkeypatch.setenv("ARENA_BASE_URL", "http://env/v1")
    monkeypatch.setenv("ARENA_API_KEY", "env-key")
    assert resolve_provider(f) == ("http://env/v1", "env-key")


def test_repo_models_yaml_ships_two_distinct_pools():
    from pathlib import Path
    from arena.llm import load_config, load_routes
    root = Path(__file__).resolve().parent.parent
    cfg = load_config(root / "models.yaml")
    routes = load_routes(root / "models.yaml")
    assert str(cfg["base_url"]).startswith("http")
    assert cfg["api_key_env"] == "FREELLMAPI_API_KEY"
    assert routes["red"] and routes["blue"]
    assert routes["red"][0] != routes["blue"][0]
