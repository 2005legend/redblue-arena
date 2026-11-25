from fastapi import APIRouter

router = APIRouter()


# DEBUG EXPOSURE (class: debug_exposure): a build diagnostics endpoint shipped without
# authentication. FIX: require a resolved admin session before returning anything.
@router.get("/api/debug/env")
def debug_env():
    return {
        "service": "lumen-goods",
        "version": "1.4.2",
        "db_path": "seed.db",
        "debug_secret": "FLAG{debug_env_leak}",
        "notes": "remove before deploy",
    }
