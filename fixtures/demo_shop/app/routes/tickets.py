from fastapi import APIRouter, Header

from app.db import get_conn
from app.routes.auth import current_user

router = APIRouter()


# IDOR (class: idor), second instance: support tickets leak an internal ops note.
# Ticket 1 is carol's and its status column holds FLAG{idor_ticket_log}.
# FIX: same owner check as orders - "WHERE id=? AND user_id=?".
@router.get("/api/support/tickets")
def my_tickets(authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    if not user:
        return {"error": "login required"}
    conn = get_conn()
    rows = [dict(r) for r in conn.execute("SELECT * FROM tickets WHERE user_id=?",
                                          (user["id"],)).fetchall()]
    conn.close()
    return {"tickets": rows}


@router.get("/api/support/tickets/{ticket_id}")
def get_ticket(ticket_id: int, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    if not user:
        return {"error": "login required"}
    conn = get_conn()
    row = conn.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()
    conn.close()
    if not row:
        return {"error": "ticket not found"}
    return dict(row)
