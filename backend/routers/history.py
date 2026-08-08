from __future__ import annotations
from fastapi import APIRouter
from database import get_connection, get_user_history

router = APIRouter()


@router.get("/history")
def history(user_id: str, limit: int = 50):
    conn = get_connection()
    try:
        items = get_user_history(conn, user_id, limit)
        return {"items": items}
    finally:
        conn.close()
