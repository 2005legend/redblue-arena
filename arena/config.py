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


def load_config(path: str) -> ArenaConfig:
    p = Path(path).resolve()
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    base = p.parent
    return ArenaConfig(
        app_dir=(base / raw["app_dir"]).resolve(),
        app_module=raw.get("app_module", "app.main:app"),
        seed_db=(base / raw["seed_db"]).resolve(),
        functional_tests=(base / raw["functional_tests"]).resolve(),
        users=raw.get("users", []),
        sample_ids=raw.get("sample_ids", {}),
        admin_routes=raw.get("admin_routes", []),
    )
