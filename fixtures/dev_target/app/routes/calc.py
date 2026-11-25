from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter()

_SECRET = Path(__file__).with_name("calc_secret.txt").read_text().strip()


@router.get("/api/calc")
def calc(expr: str = "1+1"):
    try:
        return {"expr": expr, "result": str(eval(expr))}
    except Exception as exc:
        raise HTTPException(400, str(exc))
