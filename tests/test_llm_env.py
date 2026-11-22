import os

from arena.llm import load_env


def test_load_env_reads_file_without_overriding(tmp_path, monkeypatch):
    f = tmp_path / ".env"
    f.write_text('# comment\nARENA_TEST_A=one\nARENA_TEST_B="two words"\nARENA_TEST_C=\nARENA_TEST_D=from_file\n')
    monkeypatch.delenv("ARENA_TEST_A", raising=False)
    monkeypatch.delenv("ARENA_TEST_B", raising=False)
    monkeypatch.delenv("ARENA_TEST_C", raising=False)
    monkeypatch.setenv("ARENA_TEST_D", "from_shell")
    load_env(f)
    assert os.environ["ARENA_TEST_A"] == "one"
    assert os.environ["ARENA_TEST_B"] == "two words"
    assert "ARENA_TEST_C" not in os.environ  # empty values are ignored
    assert os.environ["ARENA_TEST_D"] == "from_shell"
    for k in ("ARENA_TEST_A", "ARENA_TEST_B"):
        monkeypatch.delenv(k, raising=False)
