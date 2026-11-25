from fastapi import APIRouter

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
        result = eval(expr)  # noqa: S307 - demo vulnerability
        return {"expr": expr, "preview": str(result)}
    except Exception as exc:  # any failure still echoes the reason back to the client
        return {"expr": expr, "error": str(exc)}
