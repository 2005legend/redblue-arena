from pathlib import Path

from arena.config import attacker_accounts, load_config

ROOT = Path(__file__).resolve().parent.parent


def test_attacker_gets_only_one_low_privilege_account_by_default():
    cfg = load_config(str(ROOT / "arena.yaml"))
    cfg.attacker_users = []
    assert [u["username"] for u in attacker_accounts(cfg)] == ["alice"]


def test_attacker_users_can_be_named_explicitly():
    cfg = load_config(str(ROOT / "arena.yaml"))
    cfg.attacker_users = ["bob"]
    assert [u["username"] for u in attacker_accounts(cfg)] == ["bob"]


def test_flag_owners_loaded_from_yaml():
    cfg = load_config(str(ROOT / "arena.yaml"))
    assert cfg.flag_owners["FLAG{idor_invoice_leak}"] == "bob"


def test_strategy_loot_and_cache_defaults():
    cfg = load_config(str(ROOT / "arena.yaml"))
    assert cfg.strategy == "hybrid"
    assert cfg.loot_paths == ["secret.txt"]
    assert cfg.cache_path == (ROOT / "patches" / "cache.json").resolve()


def test_loot_paths_derived_from_extra_paths_when_absent(tmp_path):
    cfg_file = tmp_path / "arena.yaml"
    cfg_file.write_text(
        "app_dir: app\nseed_db: seed.db\nfunctional_tests: tests\n"
        "extra_paths: [uploads, notes.txt, .env]\n",
        encoding="utf-8",
    )
    cfg = load_config(str(cfg_file))
    assert cfg.loot_paths == ["notes.txt", ".env"]
    assert cfg.strategy == "hybrid"
    assert cfg.cache_path is None


def test_explicit_empty_loot_paths_disables_traversal(tmp_path):
    cfg_file = tmp_path / "arena.yaml"
    cfg_file.write_text(
        "app_dir: app\nseed_db: seed.db\nfunctional_tests: tests\n"
        "extra_paths: [notes.txt]\nloot_paths: []\n",
        encoding="utf-8",
    )
    assert load_config(str(cfg_file)).loot_paths == []

