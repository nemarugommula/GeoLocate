from __future__ import annotations
from fastapi import APIRouter
from models import FeedbackRequest
from database import get_connection, save_feedback

router = APIRouter()


@router.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    conn = get_connection()
    try:
        save_feedback(conn, req.lookup_id, "", req.vote, req.correct_location)
        return {"status": "saved"}
    finally:
        conn.close()
