from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class ArenaConfig:
    app_dir: Path
    app_module: str
    seed_db: Path
    functional_tests: Path
    users: list = field(default_factory=list)
    sample_ids: dict = field(default_factory=dict)
    admin_routes: list = field(default_factory=list)
    extra_paths: list = field(default_factory=list)
    attacker_users: list = field(default_factory=list)
    flag_owners: dict = field(default_factory=dict)
    strategy: str = "hybrid"
    login_path: str | None = None
    loot_paths: list = field(default_factory=list)
    cache_path: Path | None = None


def _loot_paths(raw: dict) -> list:
    if "loot_paths" in raw:  # an explicit empty list turns traversal testing off
        return list(raw["loot_paths"] or [])
    # Files copied next to the app are plausible traversal targets; directories are not.
    return [p for p in raw.get("extra_paths", [])
            if Path(p).suffix or Path(p).name.startswith(".")]


def load_config(path: str) -> ArenaConfig:
    p = Path(path).resolve()
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    base = p.parent
    cache = raw.get("cache_path")
    strategy = raw.get("strategy", "hybrid")
    if strategy not in ("hybrid", "sweep", "llm"):
        raise ValueError(f"strategy must be hybrid, sweep or llm (got {strategy!r})")
    return ArenaConfig(
        app_dir=(base / raw["app_dir"]).resolve(),
        app_module=raw.get("app_module", "app.main:app"),
        seed_db=(base / raw["seed_db"]).resolve(),
        functional_tests=(base / raw["functional_tests"]).resolve(),
        users=raw.get("users", []),
        sample_ids=raw.get("sample_ids", {}),
        admin_routes=raw.get("admin_routes", []),
        extra_paths=raw.get("extra_paths", []),
        attacker_users=raw.get("attacker_users", []),
        flag_owners=raw.get("flag_owners", {}),
        strategy=raw.get("strategy", "hybrid"),
        login_path=raw.get("login_path"),
        loot_paths=_loot_paths(raw),
        cache_path=(base / cache).resolve() if cache else None,
    )


def attacker_accounts(cfg: ArenaConfig) -> list:
    """Accounts Red may use. Default: ONE low-privilege user, so Red must break access control
    (IDOR, admin bypass) instead of simply logging in as the account that owns a secret."""
    if cfg.attacker_users:
        return [u for u in cfg.users if u["username"] in cfg.attacker_users]
    return [u for u in cfg.users if u.get("role") != "admin"][:1]
