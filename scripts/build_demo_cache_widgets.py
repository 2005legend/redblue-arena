"""Build a single widgets.py fix and verify it.

This is a one-off because the main cache builder had a typo that caused
the staging copy to fail booting after the fix was applied.

Fix: Replace the vulnerable eval() with ast parsing + safe evaluation.
"""
import httpx
import shutil

from arena.blue import Edit, _stage_and_verify, store_edits
from arena.config import load_config
from arena.referee import Exploit
from arena.sandbox import PortAllocator, TargetProcess


def main() -> None:
    cfg = load_config("arena.demo.yaml")
    cache = cfg.cache_path
    ports = PortAllocator(8400)
    work = Path("work/widgets-only")
    live = TargetProcess(cfg.app_dir, cfg.seed_db, ports.next(), work, cfg.app_module,
                         cfg.extra_paths)
    live.prepare()

    # Staging copy should have the vulnerable widgets.py; apply the fix manually
    staging_widgets = live.dir / "app" / "routes" / "widgets.py"
    old_content = staging_widgets.read_text(encoding="utf-8")
    new_content = '''from fastapi import APIRouter
import ast

router = APIRouter()

# Kept at module scope so the eval sandbox can see it; the sweep payload scans globals().
WIDGET_MASTER_KEY = "FLAG{code_injection_eval}"


# CODE INJECTION (class: code_injection): a promo widget preview evaluates the caller's
# expression server-side, so `[v for v in globals().values() if 'FLAG{' in str(v)]`
# walks module globals and returns the key.
# FIX: parse with ast and allow a small arithmetic grammar only; reject everything else.
@router.get("/api/widgets/preview")
def preview(expr: str = ""):
    try:
        node = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        return {"expr": expr, "error": f"not an expression: {exc}"}
    for sub in ast.walk(node):
        if isinstance(sub, (ast.Name, ast.Call, ast.Attribute, ast.Subscript)):
            return {"expr": expr, "error": "only numbers and arithmetic are allowed"}
    import operator as _op
    ops = {ast.Add: _op.add, ast.Sub: _op.sub, ast.Mult: _op.mul, ast.Div: _op.truediv}
    try:
        def _ev(n):
            if isinstance(n, ast.Constant):
                return n.value
            if isinstance(n, ast.BinOp):
                return ops[type(n.op)](_ev(n.left), _ev(n.right))
            if isinstance(n, ast.UnaryOp):
                return (-_ev(n.operand) if isinstance(n.op, ast.USub)
                        else _ev(n.operand))
            raise ValueError("unsupported")
        return {"expr": expr, "preview": str(_ev(node.body))}
    except Exception as exc:  # division by zero and friends, no leak either way
        return {"expr": expr, "error": str(exc)}
'''
    staging_widgets.write_text(new_content, encoding="utf-8")

    # Boot the staging copy to verify it starts
    live.start()
    try:
        openapi = httpx.get(live.url + "/openapi.json", timeout=5).json()
        assert openapi, "no openapi from the target"
        print("Staging copy booted OK")

        # Verify the exploit is blocked now
        expr = "[v for v in globals().values() if 'FLAG{' in str(v)]"
        r = httpx.get(live.url + "/api/widgets/preview", params={"expr": expr}, timeout=5)
        blocked = "error" in r.json()
        print(f"Exploit blocked? {blocked}")

        # Run the 12 frozen functional tests to ensure no regression
        import subprocess
        result = subprocess.run(
            ["python", "-m", "pytest", "-q"],
            cwd=cfg.functional_tests,
            env={**dict(__import__("os").environ), "ARENA_TARGET": live.url},
            capture_output=True,
            text=True
        )
        tests_ok = result.returncode == 0
        print(f"Functional tests passed? {tests_ok}")
        if not tests_ok:
            print(result.stdout[-500:])
            print(result.stderr[-500:])

        # If everything passes, store the edit
        if tests_ok:
            ex = Exploit("GET", "/api/widgets/preview", None, {"expr": expr}, None,
                         "FLAG{code_injection_eval}", "code_injection", None)
            store_edits(cache, ex, [Edit("app/routes/widgets.py", old_content, new_content)])
            print(f"Stored fix in cache -> {cache}")
        else:
            print("Not storing: functional tests failed")
    finally:
        live.stop()
        if work.exists():
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    from pathlib import Path
    main()
